from fastapi import APIRouter, HTTPException, Depends
from handlers.db_handler import NoloDBHandler
from handlers.ral_handler import NoloRateLimit
from handlers.s3_handler import NoloBlobAPI
from models.rdr_model import Booklet, BookletList
import os
import logging

# Create Logger
logger = logging.getLogger(__name__)

# Global Vars
MODULE_NAME = "reader"
MODULE_PREFIX = "/reader"
MODULE_TAGS = [MODULE_NAME]
MODULE_DESCRIPTION = ""
MAX_CALLS_ALLOWED_PER_MIN = 25
MAX_TIME_WAIT_429_IN_SECS = 60
MAX_PENALTY_TIME_429_IN_SECS = 180
URL_EXPIRATION_IN_SECS = os.getenv("URL_EXPIRATION_IN_SECS")

# FastAPI Instance
router = APIRouter(prefix=MODULE_PREFIX, tags=MODULE_TAGS)

# Handlers
db = NoloDBHandler()
s3 = NoloBlobAPI()

# Rate Limit 20 calls in 60 seconds
rate_limit = NoloRateLimit(
    MAX_CALLS_ALLOWED_PER_MIN, MAX_TIME_WAIT_429_IN_SECS, MAX_PENALTY_TIME_429_IN_SECS
)

# Dependencies
RATE_LIMIT = Depends(rate_limit)

# Models


# Environment


# Routes
@router.get("", dependencies=[RATE_LIMIT])
def index():
    return {
        "mesagge": f"Hello to module: {MODULE_NAME}",
        "module": MODULE_NAME,
    }


@router.get("/ping", dependencies=[RATE_LIMIT])
def ping():
    return {"message": "pong", "module": MODULE_NAME}


# URI for Return all the Documents id, Name, Cover Page Thumbnail
@router.get("/bookshelf", response_model=BookletList, dependencies=[RATE_LIMIT])
def return_all_documents() -> dict:
    """
    return a JSON struct with all doc
    """
    try:
        table = db.get_table()
        response = table.scan(
            ProjectionExpression="doc_id, doc_name, doc_title, doc_description, number_of_pages,owner_id, created_at, modify_at, cover_img, is_published, tts_ready"
        )
        data = response["Items"]
        # data = response["Count"]

        # TODO: Calculate Presigned URL for Cover
        for item in data:
            img_file_key = f"img/{item['doc_id']}/{item['doc_id']}_page_01.png"
            cover_img = s3.generate_presigned_url(img_file_key)
            item["cover_img"] = cover_img

        if not data:
            logger.warning("No Data in Table")
            raise HTTPException(status_code=404, detail=" Not Data in Table")
        return data
    except Exception as e:
        logger.error(f"No Data Found REASON: {e}", extra={"error": e})
        raise HTTPException(status_code=404, detail=" Not Data in Table")


@router.get("/bookshelf/{item_id}", response_model=Booklet, dependencies=[RATE_LIMIT])
async def return_one_item(item_id: str):
    """
    GET One Item
    """
    table = db.get_table()
    response = table.get_item(Key={"doc_id": item_id})
    item = response.get("Item")

    # Recalculate the presigned URL for each page
    for page in item["pages"]:
        page_name = page["file_name"]
        hashed_name = page["master_doc"]
        tts_file_key = f"tts/{hashed_name}/{page_name[:-4]}.mp3"
        img_file_key = f"img/{hashed_name}/{page_name}"
        img_tts_file = page_name[:8] + "_img_desc" + page_name[8:-4] + ".mp3"
        img_tts_file_key = f"tts/{hashed_name}/{img_tts_file}"
        txt_file_key = f"txt/{hashed_name}/{page_name[:-4]}.txt"
        tts_url = s3.generate_presigned_url(tts_file_key)
        img_url = s3.generate_presigned_url(img_file_key)
        txt_url = s3.generate_presigned_url(txt_file_key)
        img_tts_url = s3.generate_presigned_url(img_tts_file_key)
        page["elements"]["img_url"] = img_url
        page["elements"]["tts_url"] = tts_url
        page["elements"]["txt_file_url"] = txt_url
        page["elements"]["img_tts_url"] = img_tts_url

    if not item:
        raise HTTPException(status_code=404, detail=f" Not item {item_id} in Table")

    return item
