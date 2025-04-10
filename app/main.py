from dotenv import load_dotenv
from fastapi import FastAPI
from mangum import Mangum

from app.api.v1.endpoints import router as v1_router

# Load environment variables from .env (for local dev)
load_dotenv()

app = FastAPI()

# route grouping under /api/v1
app.include_router(v1_router, prefix="/api/v1")

# deploying to Lambda with Mangum:
handler = Mangum(app)
