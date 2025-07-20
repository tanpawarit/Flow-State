"""
Webhook event validation utilities.
"""

import logging
from typing import Any, Dict, List

from pydantic import ValidationError

from src.webhooks.shared.base_models import BaseWebhookEvent
from src.webhooks.shared.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)


class WebhookEventValidator:
    """Utility class for validating webhook events."""

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """
        Validate that required fields are present in webhook data.

        Args:
            data: Webhook payload data
            required_fields: List of required field names

        Raises:
            WebhookValidationError: If any required field is missing
        """
        missing_fields = []

        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise WebhookValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    @staticmethod
    def validate_event_structure(
        event_data: Dict[str, Any], event_class: type, provider: str
    ) -> BaseWebhookEvent:
        """
        Validate webhook event data against a Pydantic model.

        Args:
            event_data: Raw webhook event data
            event_class: Pydantic model class to validate against
            provider: Name of webhook provider

        Returns:
            Validated event instance

        Raises:
            WebhookValidationError: If validation fails
        """
        try:
            return event_class(**event_data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_details.append(f"{field}: {message}")

            raise WebhookValidationError(
                f"Event validation failed: {'; '.join(error_details)}",
                provider=provider,
            )
        except Exception as e:
            raise WebhookValidationError(
                f"Unexpected validation error: {e}", provider=provider
            )

    @staticmethod
    def validate_event_type(
        event_type: str, supported_types: List[str], provider: str
    ) -> None:
        """
        Validate that event type is supported by provider.

        Args:
            event_type: Event type from webhook
            supported_types: List of supported event types
            provider: Name of webhook provider

        Raises:
            WebhookValidationError: If event type is not supported
        """
        if event_type not in supported_types:
            raise WebhookValidationError(
                f"Unsupported event type '{event_type}'. Supported types: {', '.join(supported_types)}",
                provider=provider,
            )

    @staticmethod
    def validate_payload_size(payload: bytes, max_size_mb: int = 10) -> None:
        """
        Validate webhook payload size.

        Args:
            payload: Raw webhook payload
            max_size_mb: Maximum allowed size in MB

        Raises:
            WebhookValidationError: If payload is too large
        """
        size_bytes = len(payload)
        max_size_bytes = max_size_mb * 1024 * 1024

        if size_bytes > max_size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            raise WebhookValidationError(
                f"Payload too large: {size_mb:.2f}MB (max: {max_size_mb}MB)"
            )

    @staticmethod
    def sanitize_webhook_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize webhook data by removing sensitive fields.

        Args:
            data: Raw webhook data

        Returns:
            Sanitized data with sensitive fields removed or masked
        """
        sensitive_fields = [
            "password",
            "token",
            "secret",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "authorization",
        ]

        sanitized = data.copy()

        def _sanitize_dict(d: Dict[str, Any]) -> None:
            for key, value in d.items():
                if isinstance(value, dict):
                    _sanitize_dict(value)
                elif isinstance(value, str) and any(
                    field in key.lower() for field in sensitive_fields
                ):
                    d[key] = "***REDACTED***"

        _sanitize_dict(sanitized)
        return sanitized
