# Plane → Discord Webhook Bridge

Small, reusable bridge that receives Plane webhooks and forwards them to Discord with nice embeds and optional project filtering.

## Features

- Signature verification (`X-Plane-Signature`)
- Clean Discord embeds (project, state, priority, assignee, link)
- Optional project allowlist (comma-separated)
- Returns proper 200 to Plane

## Configuration (1Password)

Create two items in the `home-cluster` vault:

| Item                        | Field              | Description                                      |
|----------------------------|--------------------|--------------------------------------------------|
| `kanban-discord-webhook`   | `webhook-url`      | Discord incoming webhook URL                     |
| `kanban-discord-webhook`   | `allowed-projects` | Comma-separated project names (e.g. `HC`)        |
| `plane-webhook-secret`     | `secret`           | Signing secret from Plane (from the CSV download)|

## Internal URL

When creating the webhook in Plane, use:

```
http://plane-webhook-bridge.plane-webhook.svc.cluster.local:8000/webhook
```

## Deployment

This component is deployed via Flux under `home-cluster/plane-webhook/`.

## Environment Variables (in pod)

| Variable               | Required | Description |
|------------------------|----------|-------------|
| `DISCORD_WEBHOOK_URL`  | Yes      | From secret |
| `PLANE_WEBHOOK_SECRET` | Yes      | From secret |
| `ALLOWED_PROJECTS`     | No       | Comma-separated list (case-insensitive) |

## Example Embed

```
Issue created
Fix login bug

Project     Home Cluster
State       In Progress
Priority    High
Assignee    Steve
```

## License

MIT (or whatever you prefer)