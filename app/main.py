from fastapi import FastAPI
from settings.apiconfig import NOLOConfig
from router import admin, reader, file_api
import uvicorn
from mangum import Mangum


#Load Config
api_config = NOLOConfig()

# Declare fastAPI

app =  FastAPI(
    title=api_config.title,
    version=api_config.version,
    description=api_config.description,
    root_path=api_config.root_path,
)

# For Serverles Lambda 
handler = Mangum(app)

# Router
app.include_router(admin.router)
app.include_router(reader.router)
app.include_router(file_api.router)

# Run the API Server
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
