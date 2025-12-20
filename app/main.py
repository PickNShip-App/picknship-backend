from fastapi import FastAPI
from app.api import auth, webhook, stores, rates, success, orders
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Pick'NShip API")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

app.include_router(success.router)
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(stores.router)
app.include_router(rates.router)
app.include_router(orders.router)

@app.get("/")
def home():
    return {"message": "Pick'NShip backend running 🚀"}