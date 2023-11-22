from fastapi import APIRouter, HTTPException, status, UploadFile, File
from handlers.db_handler import NoloDBHandler
from models.rdr_model import Booklet, BookletList


# fastAPI
router = APIRouter(prefix="/reader", tags=["reader"])

# Handlers
db = NoloDBHandler()

# Models


# Environment


# Routes
@router.get("")
def reader_index():
    return {"mesagge": "Hello World", "module": "reader"}


@router.get("/ping")
def ping():
    return {"message": "pong", "module": "reader"}


# TODO: Add URI for Return all the Documents id, Name, Cover Page Thumbnail
@router.get("/bookshelf", response_model=BookletList)
def return_all_documents() -> dict:
    """
    return a JSON struct with all doc
    """
    table = db.get_table()
    response = table.scan(
        ProjectionExpression="doc_id, doc_name, doc_description, number_of_pages, created_at, modify_at, cover_img"
    )
    data = response["Items"]
    # data = response["Count"]

    if not data:
        raise HTTPException(status_code=404, detail=" Not Data in Table")

    # response = dummy_data.create_multiple_docs()
    return data


@router.get("/bookshelf/{item_id}", response_model=Booklet)
async def return_one_item(item_id: str):
    """
    GET One Item
    """
    # response = dummy_data.create_single_doc()

    table = db.get_table()
    response = table.get_item(Key={"doc_id": item_id})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail=f" Not item {item_id} in Table")

    return item
