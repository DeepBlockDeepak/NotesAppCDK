from fastapi import FastAPI
from app.api.v1.endpoints import router as v1_router
from dotenv import load_dotenv
import os

# Load environment variables from .env (for local dev)
load_dotenv()

app = FastAPI()

# Example: route grouping under /api/v1
app.include_router(v1_router, prefix="/api/v1")

# If you're deploying to Lambda with Mangum:
# from mangum import Mangum
# handler = Mangum(app)
