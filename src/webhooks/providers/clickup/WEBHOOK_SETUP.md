# ClickUp Webhook Setup Guide

This guide explains how to set up ClickUp webhooks to automatically sync data with your Flow-State graph database.

## Overview

The webhook system automatically updates the Neo4j graph database when changes occur in ClickUp, providing real-time synchronization of:

- Task creation, updates, and deletion
- Assignment changes
- Status and priority updates
- Due date modifications
- Task moves between lists
- Subtask operations

## Prerequisites

1. ClickUp API access with appropriate permissions
2. A publicly accessible webhook URL (see deployment options below)
3. Valid configuration in `config.yaml`

## Configuration

### 1. Update config.yaml

Copy `example-config.yaml` to `config.yaml` and configure:

```yaml
# ClickUp Configuration
clickup:
  api_key: "pk_your_actual_api_key"
  team_id: "your_team_id"
  webhook_secret: "your_webhook_secret"  # Optional but recommended

# Webhook Server Configuration
webhooks:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  public_url: "https://your-domain.com"  # Your public webhook URL

# Neo4j Database Configuration  
neo4j:
  uri: "neo4j+s://your-instance.databases.neo4j.io"
  username: "neo4j"
  password: "your_password"
```

### 2. Generate Webhook Secret (Recommended)

For security, generate a strong webhook secret:

```bash
# Generate a random secret
python -c "import secrets; print(secrets.token_hex(32))"
```

Add this secret to both your `config.yaml` and your ClickUp webhook configuration.

## Deployment Options

### Option 1: ngrok (Development/Testing)

For testing locally:

```bash
# Install ngrok
# Start your webhook server locally
python main.py

# In another terminal, expose via ngrok
ngrok http 8000

# Use the ngrok URL (e.g., https://abc123.ngrok.io) as your webhook URL
```

### Option 2: Cloud Deployment

Deploy to any cloud provider that supports Python web applications:

- **Railway**: `railway deploy`
- **Render**: Connect your GitHub repo
- **Heroku**: `git push heroku main`
- **DigitalOcean**: App Platform
- **AWS/GCP/Azure**: Container services

## Setting Up ClickUp Webhooks

### 1. Access ClickUp Webhook Settings

1. Go to your ClickUp workspace
2. Navigate to Settings → Integrations → Webhooks
3. Click "Add Webhook"

### 2. Configure Webhook

**Endpoint URL**: `https://your-domain.com/webhooks/clickup`

**Events to Subscribe** (recommended):
- `taskCreated` - New tasks
- `taskUpdated` - Task modifications  
- `taskDeleted` - Task deletion
- `taskStatusUpdated` - Status changes
- `taskAssigneeUpdated` - Assignment changes
- `taskDueDateUpdated` - Due date changes
- `taskPriorityUpdated` - Priority changes
- `taskMoved` - Tasks moved between lists
- `subtaskCreated` - New subtasks
- `subtaskUpdated` - Subtask modifications
- `subtaskDeleted` - Subtask deletion

**Secret**: Enter the webhook secret from your config (if using)

### 3. Test Webhook

1. Save the webhook configuration in ClickUp
2. Create or modify a task in ClickUp
3. Check your application logs for webhook events:

```bash
# Check logs
tail -f /var/log/flow-state.log

# Or if running locally
python main.py
```

## Webhook Endpoints

### POST /webhooks/clickup

Main webhook endpoint that receives ClickUp events.

**Headers Required**:
- `Content-Type: application/json`
- `X-Signature: sha256=<signature>` (if webhook secret configured)

**Response**: 
```json
{
  "status": "success", 
  "message": "Webhook received and queued for processing"
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "clickup-webhooks"
}
```

### GET /webhooks/status

Webhook processing statistics.

**Response**:
```json
{
  "status": "operational",
  "stats": {
    "events_processed": 150,
    "events_failed": 2,
    "last_processed": "2024-07-20T10:30:00Z",
    "success_rate": 0.987
  }
}
```

## Supported Events

| Event | Description | Graph Updates |
|-------|-------------|---------------|
| `taskCreated` | New task created | Creates Task node and relationships |
| `taskUpdated` | Task modified | Updates Task properties |
| `taskDeleted` | Task deleted | Removes Task node and relationships |
| `taskStatusUpdated` | Status changed | Updates status property and relationship |
| `taskAssigneeUpdated` | Assignee changed | Updates ASSIGNED_TO relationships |
| `taskDueDateUpdated` | Due date changed | Updates due_date property |
| `taskPriorityUpdated` | Priority changed | Updates priority property and relationship |
| `taskMoved` | Moved between lists | Updates BELONGS_TO relationship |
| `subtaskCreated` | Subtask created | Creates Task node with SUBTASK_OF relationship |
| `subtaskUpdated` | Subtask modified | Updates subtask properties |
| `subtaskDeleted` | Subtask deleted | Removes subtask node |

## Troubleshooting

### Webhook Not Receiving Events

1. **Check URL accessibility**: Test your webhook URL:
   ```bash
   curl -X POST https://your-domain.com/webhooks/clickup \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

2. **Verify ClickUp webhook configuration**:
   - Correct endpoint URL
   - Proper events selected
   - Webhook is enabled

3. **Check application logs**:
   ```bash
   # Look for webhook events
   grep "Webhook event received" /var/log/flow-state.log
   ```

### Signature Verification Fails

1. **Check webhook secret**: Ensure the secret in config matches ClickUp
2. **Verify header**: ClickUp sends signature in `X-Signature` header
3. **Test without secret**: Temporarily remove webhook secret to test

### Database Update Fails

1. **Check Neo4j connectivity**:
   ```bash
   # Test database connection
   python -c "from src.graph.neo4j_client import Neo4jClient; client = Neo4jClient(); print('Connected!')"
   ```

2. **Verify graph schema**: Ensure required nodes (Status, Priority, etc.) exist

3. **Check ClickUp API access**: Verify API key has proper permissions

### Performance Issues

1. **Monitor processing stats**: Check `/webhooks/status` endpoint
2. **Check rate limiting**: Review ClickUp API rate limits
3. **Database performance**: Monitor Neo4j query performance

## Security Considerations

1. **Use HTTPS**: Always use HTTPS for webhook endpoints
2. **Configure webhook secret**: Enable signature verification
3. **Validate input**: All webhook data is validated with Pydantic models
4. **Rate limiting**: Consider adding rate limiting for webhook endpoints
5. **Access control**: Restrict webhook endpoint access if needed

## Testing

### Manual Testing

Test webhook processing with curl:

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhooks/clickup \
  -H "Content-Type: application/json" \
  -d '{
    "event": "taskCreated",
    "task_id": "test_task_123",
    "webhook_id": "test_webhook",
    "history_items": [],
    "task": {
      "id": "test_task_123",
      "name": "Test Task",
      "status": {"status": "TO DO"},
      "assignees": []
    }
  }'
```

### Integration Testing

1. Create a test task in ClickUp
2. Verify the task appears in your Neo4j database
3. Update the task and verify changes sync
4. Delete the task and verify removal

## Monitoring

Monitor webhook health and performance:

1. **Application logs**: Check for errors and processing stats
2. **Database monitoring**: Monitor Neo4j performance and connectivity
3. **Webhook status**: Regular checks of `/webhooks/status` endpoint
4. **ClickUp webhook logs**: Check ClickUp's webhook delivery logs

## Support

For issues:
1. Check the application logs first
2. Verify configuration settings
3. Test individual components (Neo4j, ClickUp API, webhook endpoint)
4. Review this documentation for common solutions