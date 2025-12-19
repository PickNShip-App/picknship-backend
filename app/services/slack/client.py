import httpx

async def send_slack_message(webhook_url: str, payload: dict):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json=payload)
        if resp.status_code not in (200, 201):
            raise Exception(f"Slack error: {resp.text}")
