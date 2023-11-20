from fastapi import APIRouter,HTTPException, status, UploadFile, File
from data.mockup import DUMMYData
from pydantic import BaseModel
from handlers.db_handler import NoloDBHandler





router = APIRouter(
    prefix="/reader",
    tags=["reader"]
)

# Handlers
dummy_data = DUMMYData()
db = NoloDBHandler()

# Models
class BookModel(BaseModel):
    id: str
    name: str
    


# Environment


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
    """
    table = db.get_table()
    response = table.scan()
    data = response["Items"]

    if not data:
        raise HTTPException(status_code=404, detail=" Not Data in Table")

    # response = dummy_data.create_multiple_docs()
    return {"data" : data}, status.HTTP_200_OK


@router.get("/bookshelf/{item_id}")
async def return_one_item(item_id: str):
    """
    GET One Item
    """
    #response = dummy_data.create_single_doc()

    table = db.get_table()
    response = table.get_item(Key={"doc_id" : item_id})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail=f" Not item {item_id} in Table")

    return {"data" : item }, status.HTTP_200_OK

