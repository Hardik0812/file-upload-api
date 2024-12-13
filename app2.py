# import time

# import aiofiles
# import pandas as pd
import asyncio

from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    file_location = f"files/{file.filename}"
    # async with aiofiles.open(file_location, "wb") as out_file:
    # content = await file.read()
    # await out_file.write(content)

    # Simulate long processing time
    await process_excel(file_location)

    return {"message": "File processed successfully"}

async def process_excel(file_path: str):
    # Simulate long processing time
    await asyncio.sleep(1800)  # 30 minutes (30 * 60)
    # df = pd.read_excel(file_path)
    # Process the DataFrame
    # Save or return the results
    return "Processing complete"