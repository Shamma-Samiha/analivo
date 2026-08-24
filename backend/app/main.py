from fastapi import FastAPI

from app.api.datasets import router as dataset_router
from app.api.health import router as health_router


app = FastAPI()

app.include_router(health_router)
app.include_router(dataset_router)


@app.get("/")
async def root():
    return {"message": "Analivo API is running"}