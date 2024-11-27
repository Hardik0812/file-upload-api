from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from openpyxl import load_workbook
import tempfile
import shutil
from fastapi.middleware.cors import CORSMiddleware

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
    
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")
    
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        temp_file_name = temp_file.name
        shutil.copyfileobj(file.file, temp_file)


    try:
        wb = load_workbook(temp_file_name)
        ws = wb.active


        ws["C1"] = "result"  
        for row in range(2, ws.max_row + 1):
            value = ws[f"A{row}"].value 
            ws[f"C{row}"] = value * 2 if isinstance(value, (int, float)) else "N/A"

   
        new_file_name = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx").name
        wb.save(new_file_name)
    finally:
   
        temp_file.close()

    return FileResponse(new_file_name, filename="processed_result.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
