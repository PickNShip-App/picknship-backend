from app.core.config import settings

SLACK_CHANNELS = {
    "stores": settings.SLACK_STORES_WEBHOOK_URL,
    "orders": settings.SLACK_ORDERS_WEBHOOK_URL,
}
