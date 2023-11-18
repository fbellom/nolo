from fastapi import APIRouter,HTTPException, status

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

#Routes
@router.get("/")
def admin_index():
    return {"mesagge":"Hello World"}, status.HTTP_200_OK

@router.get("/ping")
def ping():
    return {"message": "pong"}, status.HTTP_200_OK


