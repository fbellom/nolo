from typing import Dict
import time
from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
import os
from handlers.pdf_handler import NoloPDFHandler
from handlers.db_handler import NoloDBHandler
from handlers.s3_handler import NoloBlobAPI
from handlers.dep_handler import get_current_active_user
from handlers.ral_handler import NoloRateLimit
from models.iam_model import User
from models.rdr_model import Booklet, BookletEdit
import logging

# Create Logger
logger = logging.getLogger(__name__)


# Global Vars
MODULE_NAME = "booklet"
MODULE_PREFIX = "/booklet"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""
MAX_CALLS_ALLOWED_PER_MIN = 10
MAX_TIME_WAIT_429_IN_SECS = 60
MAX_PENALTY_TIME_429_IN_SECS = 300

router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers
db = NoloDBHandler()
blob = NoloBlobAPI()

# Environment
upload_path = os.getenv("UPLOAD_PATH")

# Rate Limit 10 calls in 60 seconds
rate_limit = NoloRateLimit(
    MAX_CALLS_ALLOWED_PER_MIN, MAX_TIME_WAIT_429_IN_SECS, MAX_PENALTY_TIME_429_IN_SECS
)

# Depends
PROTECTED = Depends(get_current_active_user)
RATE_LIMIT = Depends(rate_limit)


# Helper Function


def update_item_and_counter(table, item_key: Dict, attributes: Dict) -> Dict:
    # Init Update expression
    update_expression = "SET"

    # Build  expression-attributes-names and values
    expression_attrib_names = {}
    expression_attrib_values = {}
    for key, value in attributes.items():
        if key != "doc_id":
            update_expression += f" #{key} = :{key}, "
            expression_attrib_names[f"#{key}"] = key
            expression_attrib_values[f":{key}"] = value
    # Finish update-expression
    # update_expression += " update_counter = if_not_exists(update_counter, :_start) + :_inc"
    update_expression = update_expression[:-2]

    return table.update_item(
        Key=item_key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attrib_names,
        ExpressionAttributeValues=expression_attrib_values,
        ReturnValues="ALL_NEW",
    )


# Routes
@router.get("", dependencies=[PROTECTED, RATE_LIMIT])
def index(user: User = Depends(get_current_active_user)):
    return {"mesagge": "Hello World", "module": MODULE_NAME}


@router.get("/ping", dependencies=[PROTECTED, RATE_LIMIT])
def ping(user: User = Depends(get_current_active_user)):
    return {"message": "pong", "module": MODULE_NAME}


# CREATE
@router.post(
    "/upload",
    summary="Upload Booklet to be processed",
    response_model=Booklet,
    dependencies=[PROTECTED, RATE_LIMIT],
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    user: User = Depends(get_current_active_user),
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
    # Read file into memory
    file_data = await file.read()

    # Invoke PDF Handler
    pdf_handler = NoloPDFHandler(file_name=file.filename, description=description)
    # response = await pdf_handler.async_extract_text_from_file()
    response = await pdf_handler.async_extract_text_from_file(file_data)
    if not response:
        logger.error(f"Failed to extract Text from Booklet {title}")
        raise HTTPException(status_code=400, detail="Failed to extract Text from File")

    response = await pdf_handler.async_create_image_from_file(file_data)
    if not response:
        logger.error(f"Failed to extract Images from PDF {title}")
        raise HTTPException(status_code=400, detail="Failed to extract Images from PDF")

    file_metadata = pdf_handler.get_file_metadata()
    file_metadata.update(
        {
            "owner_id": user.username,
            "tts_ready": False,
            "is_published": True,
            "doc_title": title,
            "doc_description": description,
        }
    )

    # Send file_metadata to DynamoDB
    table = db.get_table()
    table.put_item(Item=file_metadata)
    logger.info(f"Booklet {file.filename} uploaded sucessfully!")
    logger.info(f"Booklet {file.filename} completed!")
    return file_metadata


# UPDATE
@router.patch(
    "/{doc_id}",
    summary="Update a Booklet",
    response_model=Booklet,
    dependencies=[PROTECTED, RATE_LIMIT],
)
async def update_one_booklet(
    doc_id: str, booklet: BookletEdit, user: User = Depends(get_current_active_user)
):
    update_doc_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Booklet Update can't be completed",
    )

    doc_not_found_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="The Booklet does not exists",
    )

    user_inactive_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is inactive",
    )

    if user.disabled:
        raise user_inactive_exception

    try:
        # Logic to Update a Record on DynamoDB
        item_key = {"doc_id": doc_id}
        table = db.get_table()
        logger.info(f"Searching Booklet {doc_id}")
        response = table.get_item(Key=item_key)

        # Extract the Document to be edited
        item = response.get("Item")

        if item is None:
            logger.warning(f"Booklet {doc_id} Not found")
            raise doc_not_found_exception
        else:
            logger.info(f"Booklet {doc_id} found")

        # Evaluate Update Cases:
        edited_pages_list = []
        edited_dict = {}

        # Capture Updates on Pages from Request
        if len(booklet.pages) > 0:
            for edit in booklet.pages:
                edited_dict = {
                    "page_num": edit.page_num,
                    "create_tts": True,
                    "elements": {
                        "text": edit.elements.text,
                        "img_text": edit.elements.img_text,
                    },
                }
                edited_pages_list.append(edited_dict)
                # Modify only the page elements marked for edition
            for page in item["pages"]:
                for elem in edited_pages_list:
                    if elem["page_num"] == page["page_num"]:
                        page["create_tts"] = elem["create_tts"]
                        page["elements"]["text"] = elem["elements"]["text"]
                        page["elements"]["img_text"] = elem["elements"]["img_text"]
                        # TODO: Recreate TTS Files for Updated Pages Only

        # Create Modified Metadata
        item["doc_title"] = booklet.doc_title
        item["doc_description"] = booklet.doc_description
        item["modify_at"] = int(time.time())
        item["owner_id"] = user.username

        # Send the Update to Database
        udpd_expr = update_item_and_counter(
            table=table, item_key=item_key, attributes=item
        )

        return {"booklet_id": doc_id, "username": user.username, "item": item}
    except Exception as e:
        logger.error(
            f"Booklet {doc_id} Update failed. Reason: {e}", extra={"error": udpd_expr}
        )
        raise update_doc_exception


@router.patch(
    "/publish/{doc_id}",
    summary="Set Visibility ON/OFF for a Booklet",
    dependencies=[PROTECTED, RATE_LIMIT],
)
async def toogle_visibility_booklet(
    doc_id: str, user: User = Depends(get_current_active_user)
):
    update_doc_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The Booklet can not be published",
    )

    doc_not_found_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="The Booklet does not exists",
    )

    user_inactive_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is inactive",
    )

    # Check if user is logged in
    if user.disabled:
        raise user_inactive_exception

    try:
        item_key = {"doc_id": doc_id}
        # Delete DynamoDB Info
        table = db.get_table()
        response = table.get_item(Key=item_key)

        # Check for Deletion
        item = response.get("Item")

        if item is None:
            logger.warning(f"Booklet {doc_id} Not found")
            raise doc_not_found_exception
        else:
            logger.info(f"Booklet {doc_id} found")

        # Toggle the state of "is_published" attribute
        logger.info(f"Booklet visibility is set to {item['is_published']}")
        item["is_published"] = not item["is_published"]  # Toggle the current State
        item["modify_at"] = int(time.time())

        logger.info(f"Booklet visibility is changed to {item['is_published']}")
        # Send the Update to Database
        udpd_expr = update_item_and_counter(
            table=table, item_key=item_key, attributes=item
        )

        return {
            "booklet_id": doc_id,
            "username": user.username,
            "is_published": item["is_published"],
            "modify_at": item["modify_at"],
        }

    except Exception as e:
        logger.error(
            f"Booklet {doc_id} Update failed. Reason: {e}", extra={"error": udpd_expr}
        )
        raise update_doc_exception


# DELETE
@router.delete(
    "/{doc_id}", summary="Delete a Booklet", dependencies=[PROTECTED, RATE_LIMIT]
)
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
        logger.error(f"Booklet {doc_id} Delete failed", extra={"error": e})
        raise delete_doc_exception
    return {"booklet_id": doc_id, "username": user.username}
