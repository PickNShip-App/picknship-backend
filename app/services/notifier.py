import httpx
from app.core.config import settings
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
import json

async def send_slack_message(
    text: str,
    blocks: Optional[list[Dict[str, Any]]] = None
) -> None:
    """
    Sends a message to Slack using Incoming Webhook.
    Never raises (notifications must NOT break business flow).
    """
    if not settings.SLACK_WEBHOOK_URL:
        return

    payload: Dict[str, Any] = {"text": text}

    if blocks:
        payload["blocks"] = blocks

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                settings.SLACK_WEBHOOK_URL,
                json=payload
            )
    except Exception as e:
        # Log only, never crash
        print(f"[WARN] Slack notification failed: {e}")



async def notify_store_installed(
    store_id: str,
    store_name: str | None = None,
    domain: str | None = None,
    email: str | None = None
):
    # Convert current time to Argentina time
    argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now_utc = datetime.now()
    now_argentina = now_utc.astimezone(argentina_tz)
    formatted_date = now_argentina.strftime("%d/%m/%Y %H:%M:%S")  # Example: 14/12/2025 03:23:37

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🎉 Nueva tienda conectada a PickNShip"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Store ID:*\n{store_id}"},
                {"type": "mrkdwn", "text": f"*Nombre:*\n{store_name or '—'}"},
                {"type": "mrkdwn", "text": f"*Dominio:*\n{domain or '—'}"},
                {"type": "mrkdwn", "text": f"*Email:*\n{email or '—'}"},
                {"type": "mrkdwn", "text": f"*Fecha:*\n{formatted_date}"},
            ]
        }
    ]

    await send_slack_message(
        text="Nueva tienda conectada a PickNShip",
        blocks=blocks
    )


async def notify_order_created(order_data: dict):
    """
    Notifica en Slack la creación de una nueva orden PickNShip.
    """

    # Convert current time to Argentina time
    argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now_utc = datetime.utcnow()
    now_argentina = now_utc.replace(tzinfo=pytz.utc).astimezone(argentina_tz)
    formatted_date = now_argentina.strftime("%d/%m/%Y %H:%M:%S")

    # Simplificar la dirección
    shipping = order_data.get("shipping_address", {})
    shipping_str = ", ".join(
        filter(None, [
            shipping.get("address"),
            shipping.get("number"),
            shipping.get("floor"),
            shipping.get("locality"),
            shipping.get("city"),
            shipping.get("province"),
            shipping.get("zipcode"),
            "AR"
        ])
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🆕 Nueva orden PickNShip: {order_data['order_id']}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Store ID:*\n{order_data['store_id']}"},
                {"type": "mrkdwn", "text": f"*Cliente:*\n{order_data.get('customer_name','—')} ({order_data.get('customer_email','—')})"},
                {"type": "mrkdwn", "text": f"*Teléfono:*\n{order_data.get('customer_phone','—')}"},
                {"type": "mrkdwn", "text": f"*Total:*\n{order_data.get('total',0.0)} {order_data.get('currency','ARS')}"},
                {"type": "mrkdwn", "text": f"*Estado:*\n{order_data.get('status','—')}"},
                {"type": "mrkdwn", "text": f"*Método de envío:*\n{order_data.get('shipping_method','—')}"},
                {"type": "mrkdwn", "text": f"*Opción de envío:*\n{order_data.get('shipping_option','—')}"},
                {"type": "mrkdwn", "text": f"*Dirección de envío:*\n{shipping_str}"},
                {"type": "mrkdwn", "text": f"*Fecha de recepción:*\n{formatted_date}"}
            ]
        }
    ]

    await send_slack_message(
        text=f"Nueva orden PickNShip: {order_data['order_id']}",
        blocks=blocks
    )


async def notify_order_updated(order_data: dict, changes: dict):
    """
    Notifica en Slack los cambios detectados en una orden.
    """
    lines = [f"📦 Orden actualizada: {order_data['order_id']} (Store {order_data['store_id']})"]
    for field, vals in changes.items():
        if field == "shipping_address":
            old_addr = json.dumps(vals["old"], indent=2) if vals["old"] else "{}"
            new_addr = json.dumps(vals["new"], indent=2) if vals["new"] else "{}"
            lines.append(f"- {field} cambiado:\nAnterior:\n{old_addr}\nNuevo:\n{new_addr}")
        else:
            lines.append(f"- {field}: {vals['old']} → {vals['new']}")
    
    message = "\n".join(lines)
    await send_slack_message(message)
