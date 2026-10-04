import os
import hmac
import hashlib
import json
from typing import Optional

import httpx
from fastapi import FastAPI, Request, HTTPException, Header

app = FastAPI(title="Plane → Discord Webhook Bridge")

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
PLANE_WEBHOOK_SECRET = os.environ.get("PLANE_WEBHOOK_SECRET", "").encode()

# Comma-separated list of allowed project names (case-insensitive)
ALLOWED_PROJECTS = [
    p.strip().lower() for p in os.environ.get("ALLOWED_PROJECTS", "").split(",") if p.strip()
]

# Whether to require and verify X-Plane-Signature
VERIFY_SIGNATURE = os.environ.get("VERIFY_SIGNATURE", "true").lower() == "true"

def verify_signature(payload: bytes, signature: str) -> bool:
    if not PLANE_WEBHOOK_SECRET or not signature:
        return False
    mac = hmac.new(PLANE_WEBHOOK_SECRET, msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)

def build_discord_embed(payload: dict) -> dict:
    event = payload.get("event", "unknown")
    action = payload.get("action", "unknown")
    data = payload.get("data", {})
    actor = payload.get("activity", {}).get("actor", {})

    actor_name = actor.get("display_name", "Unknown")

    name = data.get("name") or data.get("sequence_id") or "Untitled"
    project = data.get("project_detail", {}).get("name", "")
    state = data.get("state_detail", {}).get("name", "")
    priority = data.get("priority_detail", {}).get("name", "")
    assignee = data.get("assignees", [{}])[0].get("display_name", "") if data.get("assignees") else ""

    embed = {
        "title": f"{event.title()} {action}",
        "description": f"**{name}**",
        "color": 0x5865F2,
        "footer": {"text": f"by {actor_name}"},
    }

    fields = []
    if project:
        fields.append({"name": "Project", "value": project, "inline": True})
    if state:
        fields.append({"name": "State", "value": state, "inline": True})
    if priority:
        fields.append({"name": "Priority", "value": priority, "inline": True})
    if assignee:
        fields.append({"name": "Assignee", "value": assignee, "inline": True})

    if fields:
        embed["fields"] = fields

    if "id" in data and "project" in data:
        embed["url"] = f"https://kanban.kube.stevearnett.com/tasks/browse/{data.get('sequence_id', data['id'])}/"

    return embed

@app.post("/webhook")
async def handle_webhook(
    request: Request,
    x_plane_signature: Optional[str] = Header(None, alias="X-Plane-Signature"),
):
    body = await request.body()

    if VERIFY_SIGNATURE and PLANE_WEBHOOK_SECRET:
        if not x_plane_signature or not verify_signature(body, x_plane_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Project filter
    if ALLOWED_PROJECTS:
        project_name = payload.get("data", {}).get("project_detail", {}).get("name", "").lower()
        if project_name not in ALLOWED_PROJECTS:
            return {"status": "ignored", "reason": "project not allowed"}

    embed = build_discord_embed(payload)

    discord_payload = {
        "embeds": [embed],
        "username": "Plane",
        "avatar_url": "https://app.plane.so/favicon.ico",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            DISCORD_WEBHOOK_URL,
            json=discord_payload,
            timeout=15.0,
        )
        if resp.status_code not in (200, 204):
            raise HTTPException(status_code=502, detail=f"Discord error: {resp.status_code}")

    return {"status": "ok"}
