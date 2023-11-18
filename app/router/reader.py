from fastapi import APIRouter,HTTPException, status
from data.mockup import DUMMYData

router = APIRouter(
    prefix="/reader",
    tags=["reader"]
)

# Handlers
dummy_data = DUMMYData()


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
