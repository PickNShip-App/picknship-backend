import json
from datetime import datetime
import pytz
from app.services.slack.client import send_slack_message
from app.services.slack.channels import SLACK_CHANNELS

ORDERS_CHANNEL = "#orders"  # canal donde se envían las notificaciones de órdenes

def format_address(address: dict) -> str:
    """
    Convierte la dirección en un string legible.
    Solo incluye lo importante: calle, número, piso, ciudad, provincia, país, código postal.
    """
    if not address:
        return "—"
    parts = [
        address.get("address", ""),
        address.get("number", ""),
        f"Depto {address['floor']}" if address.get("floor") else "",
        address.get("locality", ""),
        address.get("city", ""),
        address.get("province", ""),
        address.get("country", ""),
        address.get("zipcode", "")
    ]
    # Filtrar vacíos y unir
    return ", ".join([p for p in parts if p]).strip() or "—"


async def notify_order_created(order_data: dict):
    argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now_argentina = datetime.utcnow().astimezone(argentina_tz)
    formatted_date = now_argentina.strftime("%d/%m/%Y %H:%M:%S")

    shipping_address_str = format_address(order_data.get("shipping_address", {}))

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📦 Nueva orden PickNShip"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Orden ID:*\n{order_data['order_id']}"},
                {"type": "mrkdwn", "text": f"*Store ID:*\n{order_data['store_id']}"},
                {"type": "mrkdwn", "text": f"*Cliente:*\n{order_data.get('customer_name', '—')}"},
                {"type": "mrkdwn", "text": f"*Email:*\n{order_data.get('customer_email', '—')}"},
                {"type": "mrkdwn", "text": f"*Teléfono:*\n{order_data.get('customer_phone', '—')}"},
                {"type": "mrkdwn", "text": f"*Total:*\n{order_data.get('total', 0.0)} {order_data.get('currency', 'ARS')}"},
                {"type": "mrkdwn", "text": f"*Estado:*\n{order_data.get('status', '—')}"},
                {"type": "mrkdwn", "text": f"*Método de envío:*\n{order_data.get('shipping_method', '—')}"},
                {"type": "mrkdwn", "text": f"*Opción de envío:*\n{order_data.get('shipping_option', '—')}"},
                {"type": "mrkdwn", "text": f"*Dirección de envío:*\n{shipping_address_str}"},
                {"type": "mrkdwn", "text": f"*Fecha:*\n{formatted_date}"}
            ]
        }
    ]

    payload = {
        "text": f"Nueva orden PickNShip: {order_data['order_id']}",
        "blocks": blocks
    }


    await send_slack_message(SLACK_CHANNELS["orders"], payload)


async def notify_order_updated(order_diff: dict):
    argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now_argentina = datetime.utcnow().astimezone(argentina_tz)
    formatted_date = now_argentina.strftime("%d/%m/%Y %H:%M:%S")

    changes_lines = []
    for field, change in order_diff.get("changes", {}).items():
        old_val = change.get("old", "—")
        new_val = change.get("new", "—")
        changes_lines.append(f"*{field}*: {old_val} → {new_val}")

    if not changes_lines:
        changes_lines.append("No se detectaron cambios visibles.")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "✏️ Orden PickNShip actualizada"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Orden ID:*\n{order_diff['order_id']}"},
                {"type": "mrkdwn", "text": f"*Store ID:*\n{order_diff['store_id']}"},
                {"type": "mrkdwn", "text": f"*Cambios:*\n" + "\n".join(changes_lines)},
                {"type": "mrkdwn", "text": f"*Fecha:*\n{formatted_date}"}
            ]
        }
    ]

    payload = {
        "text": f"Orden actualizada PickNShip: {order_diff['order_id']}",
        "blocks": blocks
    }

    await send_slack_message(SLACK_CHANNELS["orders"], payload)

