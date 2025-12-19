from datetime import datetime
import pytz
from app.services.slack.client import send_slack_message
from app.services.slack.channels import SLACK_CHANNELS

async def notify_store_installed(store_id, store_name=None, domain=None, email=None):
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    now = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")

    payload = {
        "text": "Nueva tienda conectada a PickNShip",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎉 Nueva tienda conectada"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Store ID:*\n{store_id}"},
                    {"type": "mrkdwn", "text": f"*Nombre:*\n{store_name or '—'}"},
                    {"type": "mrkdwn", "text": f"*Dominio:*\n{domain or '—'}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{email or '—'}"},
                    {"type": "mrkdwn", "text": f"*Fecha:*\n{now}"},
                ]
            }
        ]
    }

    await send_slack_message(SLACK_CHANNELS["stores"], payload)
