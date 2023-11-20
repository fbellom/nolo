from fastapi import APIRouter,HTTPException, status, UploadFile, File
import os
from handlers.pdf_handler import NoloPDFHandler
from handlers.db_handler import NoloDBHandler


router = APIRouter(
    prefix="/file",
    tags=["file"]
)

# Handlers
db = NoloDBHandler()

# Environment
upload_path=os.getenv("UPLOAD_PATH")

#Routes
@router.get("/")
def file_index():
    return {"mesagge":"Hello World", "module" : "file"}, status.HTTP_200_OK

@router.get("/ping")
def ping():
    return {"message": "pong",  "module" : "file"}, status.HTTP_200_OK


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Validate PDF File
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    # Save File Locally
    file_location =f"{upload_path}/{file.filename}"
    with open(file_location, 'wb') as file_object:
        file_object.write(file.file.read())

    # TODO:
    # Invoke PDF Handler
    pdf_handler =NoloPDFHandler(file_name=file.filename,path=upload_path)
    response = await pdf_handler.async_extract_text_from_file()
    if not response:
        raise HTTPException(status_code=400, detail="Failed to extract Text from File")
    
    response = await pdf_handler.async_create_image_from_file()
    if not response:
        raise HTTPException(status_code=400, detail="Failed to extract Images from PDF")
    
    file_metadata = pdf_handler.get_file_metadata()
    # 
    # TODO: Invoke S3 Handler to upload the img ad the txt files    

    # TODO: Send file_metadata to DynamoDB
    table = db.get_table()
    table.put_item(Item=file_metadata)

    return {"data": file_metadata}, status.HTTP_201_CREATED
