from fastapi import APIRouter,HTTPException, status, UploadFile, File
from data.mockup import DUMMYData
import os
from handlers.pdf_handler import NoloPDFHandler




router = APIRouter(
    prefix="/reader",
    tags=["reader"]
)

# Handlers
dummy_data = DUMMYData()

# Environment
upload_path=os.getenv("UPLOAD_PATH")

#Routes
@router.get("/")
def reader_index():
    return {"mesagge":"Hello World", "module" : "reader"}, status.HTTP_200_OK

@router.get("/ping")
def ping():
    return {"message": "pong",  "module" : "reader"}, status.HTTP_200_OK



# TODO: Add URI for Return all the Documents id, Name, Cover Page Thumbnail
@router.get("/bookshelf")
def return_all_documents()->dict:
    """
    return a JSON struct with all doc
    { 'data' :
     [
      {
        'name' : 'document 1',
        'doc_id' : 'hAsHedNamed00',
        'thumbnail_img_url: 'https://url.to.img'
      },
      ...
     ]
    }
    """
    response = dummy_data.create_multiple_docs()
    return {"data" : response}, status.HTTP_200_OK


@router.get("/bookshelf/{item_id}")
async def return_one_item(item_id: str):
    """
    GET One Item
    """
    response = dummy_data.create_single_doc()

    return {"data" : response }, status.HTTP_200_OK


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

    return {"data": file_metadata}, status.HTTP_201_CREATED
