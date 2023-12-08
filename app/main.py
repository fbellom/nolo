from fastapi import FastAPI
from settings.nolo_config import NoloCFG
from router import booklet, reader, token, sign, tts
import uvicorn
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging


# Declare a Logger
logger = logging.getLogger(__name__)

# Load Config
api_config = NoloCFG()

# Declare fastAPI

app = FastAPI(
    title=api_config.title,
    version=api_config.version,
    description=api_config.description,
    root_path=api_config.root_path,
)



# Midelleware
# Allow these origins to access the API
ORIGINS = [
    "http://localhost",
    "https://localhost:3000",
    "https://www.noloreader.org",
    "https://www.nololector.org",
]

# Allow these methods to be used
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

# Only these headers are allowed
# headers = ["Content-Type", "Authorization"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=METHODS,
    allow_headers=["*"],
)

# Entry Point
@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url='/api/docs')

# For Serverles Lambda
handler = Mangum(app)

# Router
app.include_router(token.router)
app.include_router(sign.router)
app.include_router(reader.router)
app.include_router(booklet.router)
# app.include_router(tts.router)
# app.include_router(cloudmanager.router)


# Run the API Server
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
