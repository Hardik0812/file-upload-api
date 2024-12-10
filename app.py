import os
import re

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

from utils import clean_phone_number, query_cnam_api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend's URL for stricter rules, e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Use specific methods like ["GET", "POST"] if needed
    allow_headers=["*"],  # Specify headers if needed
)

# Define the upload folder
UPLOAD_FOLDER = "./uploads"
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def clean_name(name):
    return re.findall(r"\w+", name.upper())


def process_file(file_path):
    df = pd.read_excel(file_path)

    valid_headers = ["phone n", "phonen"]
    headers = [col for col in df.columns]
    phone_columns = [
        col
        for col in headers
        if re.fullmatch(r"(Relative\s?\d*\s?)?[Pp]hone\s?\d+$", col)
    ]

    new_column = ["", ""]
    for phone_column in phone_columns:
        new_column.append(phone_column + "No")
        new_column.append(phone_column + "API Name")

    new_column.append("")
    new_column.append("")

    for phone_column in phone_columns:
        new_column.append(phone_column + "No")
        new_column.append(phone_column + "API Name")

    updated_columns = df.columns.tolist() + new_column
    df = df.reindex(columns=updated_columns)
    df.to_excel(file_path, index=False)

    wb = load_workbook(file_path)
    sheet = wb.active

    relative_values = list()
    for phone_column in phone_columns:
    
        relative_value = re.split(r'(?<=\d) ', phone_column)[0]
        relative_values.append(relative_value)


    for index, row in df.iterrows():
        for int_idx, column in enumerate(phone_columns):
            phone_number = row[column]
            print("phone_number",phone_number)
            clean_number = clean_phone_number(str(phone_number))
            print("clean_number",clean_number[0:10])
            api_response = query_cnam_api(clean_number)

            api_name = api_response.get("name", "").upper()
            api_name_parts = clean_name(api_name)

            
            # for relative_value in relative_values:
            first_name_column = f"{relative_values[int_idx]} First Name" if "Relative" in relative_values[int_idx] else "First Name"
            last_name_column = f"{relative_values[int_idx]} Last Name" if "Relative" in relative_values[int_idx] else "Last Name"
            excel_name_parts = clean_name(f"{row[first_name_column]} {row[last_name_column]}")


            # excel_name_parts = clean_name(f"{row['First Name']} {row['Last Name']}")

            is_match = any(api_part in excel_name_parts for api_part in api_name_parts)
            light_green_fill = PatternFill(
                start_color="CCFFCC", end_color="CCFFCC", fill_type="solid"
            )
            light_red_fill = PatternFill(
                start_color="FFCCCC", end_color="FFCCCC", fill_type="solid"
            )

            if is_match:
                col_index = len(row) - (len(phone_columns) * 4) + (int_idx * 2) - 1
                sheet.cell(index + 2, col_index).value = clean_number
                sheet.cell(index + 2, col_index + 1).value = api_name
                sheet.cell(index + 2, col_index + 1).fill = light_green_fill
            elif not is_match:
                col_index = len(row) - (len(phone_columns) * 2) + (int_idx * 2) + 1
                sheet.cell(index + 2, col_index).value = clean_number
                sheet.cell(index + 2, col_index + 1).value = api_name
                sheet.cell(index + 2, col_index + 1).fill = light_red_fill

    wb.save(file_path)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Check if the file is an xlsx file
    if file.filename.split(".")[-1].lower() != "xlsx":
        return JSONResponse(
            content={"error": "Only xlsx files are allowed"}, status_code=400
        )

    # Remove any existing files in the upload folder
    for existing_file in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, existing_file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Save the file to the upload folder
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Process the uploaded file
    process_file(file_path)

    # Send the processed file as a response
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="processed_file.xlsx",
    )
    # return StreamingResponse(
    #         file_path,
    #         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #         headers={
    #             "Content-Disposition": "attachment; filename=processed_excel.xlsx"
    #         })
