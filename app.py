from io import BytesIO
import uvicorn

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openpyxl.styles import PatternFill
from fastapi.responses import StreamingResponse
from utils import clean_phone_number, query_cnam_api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_name(name):
    """Cleans special characters and splits names into parts."""
    return name.replace("?", "").replace(",", "").strip().upper().split()


@app.post("/upload/")
async def upload_excel(file: UploadFile = File(...)):

    try:
        # Load the Excel file into pandas
        content = await file.read()
        data = pd.read_excel(BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {e}")

    # Columns to process for phone numbers
    phone_columns = ["Phone1", "Phone2", "Phone3"]

    # Clean phone numbers
    for col in phone_columns:
        data[col] = data[col].apply(clean_phone_number)

    print("col",col)
    # Create a list to store results for the second sheet
    response_data = []

    # Iterate over phone numbers and query the API
    for index, row in data.iterrows():
        for col in phone_columns:
            phone = row[col]
            print("phone",phone)
            if phone:
                # Query the API
                response = query_cnam_api(phone)
                print("response",response)
                
                if response:
                    api_name = response.get("name", "").upper()
                    excel_first_name = row['First Name'].split()[0].upper()  # Extract Excel first name
                    excel_last_name = row['Last Name'].split()[-1].upper()  # Extract Excel last name

                    # Clean and split API name
                    api_name_cleaned = api_name.replace("?", "").replace(",", "").strip()
                    print("api_name_cleaned", api_name_cleaned)
                    api_name_parts = clean_name(api_name_cleaned)  # Example: ['ROBO', 'TUCKER', 'LA']

                    # Clean and split Excel name
                    excel_name_parts = clean_name(f"{row['First Name']} {row['Last Name']}")  # Example: ['LAWRENCE', 'TUCKER']

                    # Match if any part of API name matches any part of Excel name
                    is_match = any(api_part in excel_name_parts for api_part in api_name_parts)
                # if response:

                #     api_name = response.get("name", "").upper()
                #     excel_first_name = row['First Name'].split()[0].upper()  # Extract Excel first name
                #     excel_last_name = row['Last Name'].split()[-1].upper()  # Extract Excel last name

                #     # Clean and split the API name
                #     api_name_cleaned = api_name.replace("?", "").replace(",", "").strip()
                #     print("api_name_cleaned",api_name_cleaned)
                #     api_parts = api_name_cleaned.split()

                #     # Extract API first and last names
                #     # api_first_name = api_parts[0] if len(api_parts) > 0 else ""
                #     # api_last_name = api_parts[-1] if len(api_parts) > 1 else ""
                #     # api_third_name = api_parts[1] if len(api_parts) > 2 else ""
                #     api_name_parts = clean_name(api_name)  # Example: ['ROBO', 'TUCKER', 'LA']
                #     excel_name_parts = clean_name(excel_name)

                #     # Match conditions: Either first names match or last names match
                #     is_match = (
                #                 api_first_name == excel_first_name or   # API first name matches Excel first name
                #                 api_first_name == excel_last_name or    # API first name matches Excel last name
                #                 api_third_name == excel_first_name or   # API middle/third name matches Excel first name
                #                 api_third_name == excel_last_name or    # API middle/third name matches Excel last name
                #                 api_last_name == excel_last_name or     # API last name matches Excel last name
                #                 api_last_name == excel_first_name       # API last name matches Excel first name
                #             )
                                
                    

                    # Append the data for the second sheet
                    response_data.append(
                        {
                            "Row": index + 2,  # Excel row starts from 1, header row + 1
                            "Phone Column": col,
                            "Phone Number": phone,
                            "API Name": response.get("name", ""),
                            "Excel Name": f"{row['First Name']} {row['Last Name']}",
                            "Match": "Yes" if is_match else "No",
                        }
                    )

    print("response_data",response_data)
    # Create an Excel output
    output_file = BytesIO()
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Original Data", index=False)
        response_df = pd.DataFrame(response_data)
        response_df.to_excel(writer, sheet_name="API Responses", index=False)

        # Access the workbook and apply conditional formatting
        wb = writer.book
        ws = wb["API Responses"]

        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

        # Apply conditional formatting
        for row in range(2, ws.max_row + 1):  # Skip header row
            match_cell = ws[f"F{row}"]  # "Match" column
            if match_cell.value == "Yes":
                for col in range(1, ws.max_column + 1):
                    ws.cell(row=row, column=col).fill = green_fill
            else:
                for col in range(1, ws.max_column + 1):
                    ws.cell(row=row, column=col).fill = red_fill

        # Save the workbook to the output stream
        wb.save(output_file)

    # Reset file pointer for download
    output_file.seek(0)

    # Return as a streaming response
    return StreamingResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=processed_excel.xlsx"}
    )

if __name__ == "__main__":
    # Use the PORT environment variable for Cloud Run compatibility
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)