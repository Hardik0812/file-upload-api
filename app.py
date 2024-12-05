import re
from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from utils import clean_phone_number, query_cnam_api

app = FastAPI()


def clean_name(name):
    return re.findall(r"\w+", name.upper())


@app.post("/upload/")
async def upload_excel(file: UploadFile = File(...)):
    try:
        # Read file content
        content = await file.read()

        # Check file extension
        if file.filename.endswith((".xls", ".xlsx")):
            # Read Excel file
            data = pd.read_excel(BytesIO(content))
        elif file.filename.endswith(".csv"):
            # Read CSV file
            data = pd.read_csv(BytesIO(content))
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload Excel or CSV files.",
            )

        print(data, "data")
        # Filter columns to include only "Phone n" or "Phonen" (e.g., Phone 1, Phone1, Phone 2, Phone2, etc.)
        phone_columns = [
            col
            for col in data.columns
            if re.fullmatch(r"(Relative\d* )?Phone ?\d+$", col, re.IGNORECASE)
        ]

        print("phone_columns", phone_columns)
        if not phone_columns:
            return {
                "message": "No columns matching 'Phone n' or 'Phonen' found in the uploaded file."
            }

        # Add Result columns for each Phone column
        for phone_column in phone_columns:
            result_column = f"{phone_column} Result"
            data[result_column] = ""  # Initialize the Result columns

        # Process phone data and populate results
        for _, row in data.iterrows():
            for phone_column in phone_columns:
                phone = row[phone_column]
                print("phone", phone)
                phone_str = str(phone)

                cleaned_phone = clean_phone_number(phone_str)

                print("cleaned_phone", cleaned_phone)

                # If phone number is not NaN
                api_response = query_cnam_api(cleaned_phone)
                print("api_response", api_response)

                if api_response:
                    api_name = api_response.get("name", "").upper()
                    api_name_parts = clean_name(api_name)
                    excel_name_parts = clean_name(
                        f"{row['First Name']} {row['Last Name']}"
                    )
                    is_match = any(
                        api_part in excel_name_parts for api_part in api_name_parts
                    )

                    data.at[row.name, f"{phone_column} Result"] = (
                        "Yes" if is_match else "No"
                    )
                    data.at[row.name, f"{phone_column} API Name"] = api_name

        reordered_columns = []
        for phone_column in phone_columns:
            reordered_columns.append(f"{phone_column} API Name")
            reordered_columns.append(f"{phone_column} Result")

        other_columns = [col for col in data.columns if col not in reordered_columns]
        final_columns = other_columns + reordered_columns
        data = data[final_columns]

        # Save to a new Excel sheet with formatting
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            data.to_excel(writer, index=False, sheet_name="Processed Data")
            worksheet = writer.sheets["Processed Data"]

            # Apply conditional formatting for result columns
            for phone_column in phone_columns:
                result_column = f"{phone_column} Result"
                api_name_column = f"{phone_column} API Name"
                result_col_idx = data.columns.get_loc(result_column) + 1
                api_name_col_idx = data.columns.get_loc(api_name_column) + 1

                for row_idx in range(2, len(data) + 2):  # Skip header row
                    # Format Result column
                    result_cell = worksheet.cell(row=row_idx, column=result_col_idx)
                    if result_cell.value == "Yes":
                        result_cell.fill = PatternFill(
                            start_color="00FF00", fill_type="solid"
                        )  # Green
                        result_cell.font = Font(color="000000")  # Black text
                    elif result_cell.value == "No":
                        result_cell.fill = PatternFill(
                            start_color="FF0000", fill_type="solid"
                        )  # Red
                        result_cell.font = Font(color="FFFFFF")  # White text

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=processed_excel.xlsx"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
