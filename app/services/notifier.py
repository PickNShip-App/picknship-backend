import httpx
from app.core.config import settings
from typing import Dict, Any, Optional
from datetime import datetime

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
                {"type": "mrkdwn", "text": f"*Fecha:*\n{datetime.now().isoformat()}"},
            ]
        }
    ]

    await send_slack_message(
        text="Nueva tienda conectada a PickNShip",
        blocks=blocks
    )
