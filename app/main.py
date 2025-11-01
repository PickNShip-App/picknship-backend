from fastapi import FastAPI
from app.api import auth, webhook

app = FastAPI(title="Pick'NShip API")

app.include_router(auth.router)
app.include_router(webhook.router)

@app.get("/")
def home():
    return {"message": "Pick'NShip backend running 🚀"}
