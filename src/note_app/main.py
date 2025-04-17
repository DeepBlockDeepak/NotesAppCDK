from dotenv import load_dotenv
from fastapi import FastAPI
from mangum import Mangum

from note_app.api.v1.endpoints import router as v1_router

load_dotenv()
app = FastAPI()

app.include_router(v1_router, prefix="/api/v1")

handler = Mangum(app)
