from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import os
from handlers.pdf_handler import NoloPDFHandler
from handlers.db_handler import NoloDBHandler
from handlers.s3_handler import NoloBlobAPI
from handlers.dep_handler import get_current_active_user
from models.iam_model import User
from models.rdr_model import Booklet
from typing import Annotated
import logging

# Create Logger
logger = logging.getLogger(__name__)


# Global Vars
MODULE_NAME = "booklet"
MODULE_PREFIX = "/booklet"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""

router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers
db = NoloDBHandler()
blob = NoloBlobAPI()

# Environment
upload_path = os.getenv("UPLOAD_PATH")

# Depends
PROTECTED = Depends(get_current_active_user)


# Routes
@router.get("")
def index():
    return {"mesagge": "Hello World", "module": MODULE_NAME}


@router.get("/ping")
def ping():
    return {"message": "pong", "module": MODULE_NAME}


@router.post(
    "/upload",
    summary="Upload Booklet to be processed",
    response_model=Booklet,
    dependencies=[PROTECTED],
)
async def upload_file(
    file: UploadFile = File(...), user: User = Depends(get_current_active_user)
):
    # Exception
    file_type_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User is inactive",
    )
    user_inactive_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is inactive",
    )
    
    # Validate PDF File
    if file.content_type != "application/pdf":
        raise file_type_exception
    
    if user.disabled:
        raise user_inactive_exception
    
    # Save File Locally
    logger.info(f"Booklet {file.filename} started!")
    file_location = f"{upload_path}/{file.filename}"
    with open(file_location, "wb") as file_object:
        file_object.write(file.file.read())

    # Invoke PDF Handler
    pdf_handler = NoloPDFHandler(file_name=file.filename, path=upload_path)
    response = await pdf_handler.async_extract_text_from_file()
    if not response:
        logger.error("Failed to extract Text from PDF")
        raise HTTPException(status_code=400, detail="Failed to extract Text from File")

    response = await pdf_handler.async_create_image_from_file()
    if not response:
        logger.error("Failed to extract Images from PDF")
        raise HTTPException(status_code=400, detail="Failed to extract Images from PDF")

    file_metadata = pdf_handler.get_file_metadata()
    file_metadata.update({"owner_id": user.username})
    #

    #Send file_metadata to DynamoDB
    table = db.get_table()
    table.put_item(Item=file_metadata)
    logger.info(f"Booklet {file.filename} uploaded sucessfully!")

    # Delete Local Files
    response = pdf_handler.delete_files_objects()
    if response == False:
        logger.error(f"Failed to delete local files")
        raise HTTPException(status_code=400, detail="Failed to delete local files")
    
    logger.info(f"Booklet {file.filename} completed!")
    return file_metadata


@router.delete("/{doc_id}", summary="Delete a Booklet", dependencies=[PROTECTED])
async def delete_one_booklet(
    doc_id: str, user: User = Depends(get_current_active_user)
):
    delete_doc_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The Booklet can not be deleted",
    )

    delete_blob_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The Booklet Images and text can not be deleted",
    )

    user_inactive_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is inactive",
    )

    if user.disabled:
        raise user_inactive_exception

    try:
        # Delete DynamoDB Info
        table = db.get_table()
        table.delete_item(Key={"doc_id": doc_id})

        # Check for Deletion
        response = table.get_item(Key={"doc_id": doc_id})
        item = response.get("Item")
        if item is not None:
            raise delete_doc_exception

        # Delete Objects
        blob_prefix = ["img", "txt"]
        for prefix in blob_prefix:
            filename = f"{prefix}/{doc_id}/"
            response = blob.delete_all_objects_from_s3_folder(filename)
            if not response:
                raise delete_blob_exception
            
        logger.info(f"Booklet {doc_id} and its all related files deleted!")    
    except Exception as e:
        logger.error(f"Booklet {doc_id} Delete failed", extra={"error" : e})
        raise delete_doc_exception
    return {"deleted_booklet_id": doc_id, "username": user.username}
