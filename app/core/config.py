from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    TIENDANUBE_CLIENT_ID = os.getenv("TIENDANUBE_CLIENT_ID")
    TIENDANUBE_CLIENT_SECRET = os.getenv("TIENDANUBE_CLIENT_SECRET")
    TIENDANUBE_REDIRECT_URI = os.getenv("TIENDANUBE_REDIRECT_URI")
    PICKNSHIP_EMAIL = os.getenv("PICKNSHIP_EMAIL")
    BACKEND_URL = os.getenv("BACKEND_URL", "localhost:8000")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    LOGO_URL = os.getenv("LOGO_URL", "https://picknship.com/logo.png")
    SLACK_STORES_WEBHOOK_URL = os.getenv("SLACK_STORES_WEBHOOK_URL")
    SLACK_ORDERS_WEBHOOK_URL = os.getenv("SLACK_ORDERS_WEBHOOK_URL")
    API_KEY = os.getenv("API_KEY")

settings = Settings()