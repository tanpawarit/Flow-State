# Multi-Provider Webhook Architecture

Flow-State now supports webhooks from multiple providers through a modular, extensible architecture. This document explains the new structure and how to add new webhook providers.

## 🏗️ Architecture Overview

The webhook system is organized into three main components:

```
src/webhooks/
├── providers/          # Provider-specific implementations
│   ├── clickup/       # ClickUp webhook provider
│   ├── discord/       # Discord webhook provider (future)
│   └── github/        # GitHub webhook provider (future)
├── shared/            # Common utilities and base classes
│   ├── base_models.py
│   ├── exceptions.py
│   ├── security.py
│   └── validators.py
└── core/              # Main server and routing logic
    ├── webhook_server.py
    ├── registry.py
    └── router.py
```

## 🎯 Key Features

### 1. **Multi-Provider Support**
- Support for multiple webhook providers (ClickUp, Discord, GitHub, etc.)
- Each provider has its own isolated implementation
- Dynamic provider registration and discovery

### 2. **Unified API**
- Single webhook server handling all providers
- Consistent endpoint structure: `/webhooks/{provider_name}`
- Standardized event processing and error handling

### 3. **Provider Independence**
- Each provider can have its own configuration
- Independent enable/disable controls
- Provider-specific signature validation

### 4. **Extensible Design**
- Easy to add new providers
- Common utilities shared across providers
- Abstract base classes ensure consistency

## 📋 Current Providers

### ✅ ClickUp
- **Endpoint**: `POST /webhooks/clickup`
- **Events**: Task creation, updates, deletions, status changes, etc.
- **Status**: Fully implemented and tested

### 🚧 Future Providers
- **Discord**: User events, message events, server events
- **GitHub**: Repository events, PR events, issue events
- **Slack**: Message events, channel events, workspace events

## ⚙️ Configuration

### Multi-Provider Configuration
```yaml
webhooks:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  
  providers:
    clickup:
      enabled: true
      webhook_secret: "your_clickup_secret"
    
    discord:
      enabled: false
      webhook_secret: "your_discord_secret"
    
    github:
      enabled: false
      webhook_secret: "your_github_secret"
```

### Legacy Configuration Support
For backward compatibility, ClickUp still supports legacy configuration:
```yaml
clickup:
  webhook_secret: "your_secret"  # Auto-mapped to providers.clickup.webhook_secret
```

## 🚀 Getting Started

### 1. Enable Providers
Configure which providers you want to enable in `config.yaml`:

```yaml
webhooks:
  providers:
    clickup:
      enabled: true
      webhook_secret: "your_secret_here"
```

### 2. Start the Server
```bash
python main.py
```

The server will automatically:
- Discover and register available providers
- Create endpoints for enabled providers
- Set up proper routing and validation

### 3. Configure External Webhooks
Point your external services to the appropriate endpoints:
- **ClickUp**: `https://your-domain.com/webhooks/clickup`
- **Discord**: `https://your-domain.com/webhooks/discord` (future)
- **GitHub**: `https://your-domain.com/webhooks/github` (future)

## 📊 Monitoring & Stats

### Health Check
```bash
GET /health
```

### Provider List
```bash
GET /providers
```
Returns:
```json
{
  "all_providers": ["clickup", "discord", "github"],
  "enabled_providers": ["clickup"],
  "count": 1
}
```

### Processing Statistics
```bash
GET /stats
```
Returns:
```json
{
  "status": "operational",
  "providers": {
    "clickup": {
      "events_processed": 150,
      "events_failed": 2,
      "success_rate": 0.987,
      "last_processed": "2024-07-20T10:30:00Z"
    }
  }
}
```

## 🔧 Adding New Providers

### Step 1: Create Provider Structure
```bash
mkdir src/webhooks/providers/newprovider
touch src/webhooks/providers/newprovider/__init__.py
touch src/webhooks/providers/newprovider/models.py
touch src/webhooks/providers/newprovider/processor.py
touch src/webhooks/providers/newprovider/handlers.py
```

### Step 2: Implement Base Classes

#### models.py
```python
from src.webhooks.shared.base_models import BaseWebhookEvent, WebhookEventType

class NewProviderWebhookEvent(BaseWebhookEvent):
    # Provider-specific fields
    provider_event_type: str
    entity_id: str
    
    def __init__(self, **data):
        data["provider"] = "newprovider"
        data["event_type"] = self._normalize_event_type(data.get("provider_event_type"))
        super().__init__(**data)
    
    def get_affected_entity_id(self) -> str:
        return self.entity_id
    
    def get_affected_entity_type(self) -> str:
        return "task"  # or whatever entity type
```

#### processor.py
```python
from src.webhooks.shared.base_models import BaseWebhookProvider, WebhookProcessingResult

class NewProviderProcessor(BaseWebhookProvider):
    def get_provider_name(self) -> str:
        return "newprovider"
    
    def parse_webhook_event(self, raw_payload: Dict[str, Any]) -> BaseWebhookEvent:
        return NewProviderWebhookEvent(**raw_payload)
    
    def validate_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        # Implement provider-specific signature validation
        return True
    
    async def process_event(self, event: BaseWebhookEvent) -> WebhookProcessingResult:
        # Implement event processing logic
        pass
    
    def get_supported_events(self) -> List[str]:
        return ["event1", "event2", "event3"]
```

### Step 3: Register Provider
In `src/webhooks/providers/newprovider/__init__.py`:
```python
from src.webhooks.providers import register_provider
from .processor import NewProviderProcessor

register_provider("newprovider", NewProviderProcessor)
```

### Step 4: Add Auto-Discovery
In `src/webhooks/core/registry.py`, add to `auto_discover_providers()`:
```python
try:
    from src.webhooks.providers.newprovider import NewProviderProcessor
    self.register_provider_class("newprovider", NewProviderProcessor)
except ImportError as e:
    logger.warning(f"Failed to import NewProvider: {e}")
```

### Step 5: Add Configuration
In `example-config.yaml`:
```yaml
webhooks:
  providers:
    newprovider:
      enabled: false
      webhook_secret: "your_newprovider_secret"
```

## 🔒 Security Features

### Signature Validation
Each provider implements its own signature validation:
- **ClickUp**: HMAC SHA256 with `X-Signature` header
- **Discord**: Ed25519 signatures (future)
- **GitHub**: HMAC SHA256 with `X-Hub-Signature-256` header (future)

### Payload Validation
- Size limits (default: 10MB)
- JSON schema validation
- Required field validation
- Input sanitization

### Error Handling
- Comprehensive exception hierarchy
- Secure error messages (no sensitive data exposure)
- Proper HTTP status codes
- Detailed logging for debugging

## 🧪 Testing

### Manual Testing
```bash
# Test ClickUp webhook
curl -X POST http://localhost:8000/webhooks/clickup \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=your_signature" \
  -d '{"event": "taskCreated", "task_id": "123", "webhook_id": "abc"}'

# Test health check
curl http://localhost:8000/health

# Test provider list
curl http://localhost:8000/providers

# Test stats
curl http://localhost:8000/stats
```

### Integration Testing
Each provider should include comprehensive tests for:
- Event parsing and validation
- Signature verification
- Graph database updates
- Error handling scenarios

## 🔄 Migration from Legacy Webhook

### Automatic Migration
The new system automatically supports legacy ClickUp webhook configurations. No immediate changes required.

### Recommended Migration
1. **Update configuration** to use new provider structure
2. **Test thoroughly** with new endpoints
3. **Update external webhook URLs** to use new format
4. **Remove legacy configuration** once migration is complete

### Backward Compatibility
- Legacy imports still work: `from src.webhooks import ClickUpWebhookEvent`
- Legacy configuration automatically mapped to new structure
- Existing webhook URLs continue to work during transition

## 📈 Performance & Scalability

### Optimizations
- **Async processing**: All webhook processing is async
- **Background tasks**: Non-blocking event processing
- **Connection pooling**: Efficient database connections
- **Provider isolation**: Failures in one provider don't affect others

### Monitoring
- **Processing statistics** per provider
- **Success/failure rates** tracking
- **Performance metrics** (processing time, throughput)
- **Health checks** for each component

## 🔮 Future Enhancements

### Planned Features
1. **Rate limiting** per provider
2. **Event replay** mechanism
3. **Webhook filtering** and routing rules
4. **Enhanced monitoring** and alerting
5. **Dynamic provider loading** without restarts

### Provider Roadmap
1. **Discord Webhooks** - User and server events
2. **GitHub Webhooks** - Repository and PR events  
3. **Slack Webhooks** - Message and workspace events
4. **Custom Webhooks** - Generic webhook support

The multi-provider architecture provides a solid foundation for expanding Flow-State's webhook capabilities while maintaining clean separation of concerns and easy extensibility.