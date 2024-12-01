from io import BytesIO

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
                    # Match names
                    api_name = response.get("name", "").upper()
                    first_name = row.get("First Name", "").upper()
                    last_name = row.get("Last Name", "").upper()

                    is_match = api_name == first_name or api_name == last_name


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