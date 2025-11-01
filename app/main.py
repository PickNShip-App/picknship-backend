from fastapi import FastAPI
from app.api import auth, webhook
from app.api.stores import router as stores_router

app = FastAPI(title="Pick'NShip API")

app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(stores_router)

@app.get("/")
def home():
    return {"message": "Pick'NShip backend running 🚀"}