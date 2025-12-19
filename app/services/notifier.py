from app.services.slack.stores import notify_store_installed as slack_store_installed
from app.services.slack import orders as slack_orders


async def notify_new_store(store: dict):
    """
    Orquesta notificación de nueva tienda
    """
    await slack_store_installed(
        store_id=store["store_id"],
        store_name=store.get("name"),
        domain=store.get("domain"),
        email=store.get("email")
    )

async def notify_order_created(order_data: dict):
    await slack_orders.notify_order_created(order_data)

async def notify_order_updated(order_diff: dict):
    await slack_orders.notify_order_updated(order_diff)