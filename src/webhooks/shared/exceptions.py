"""
Custom exceptions for webhook processing.
"""

from typing import Optional


class WebhookError(Exception):
    """Base exception for all webhook-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        event_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.event_id = event_id
        self.message = message

    def __str__(self):
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.event_id:
            parts.append(f"Event ID: {self.event_id}")
        return " | ".join(parts)


class WebhookValidationError(WebhookError):
    """Raised when webhook payload validation fails."""

    pass


class WebhookSignatureError(WebhookError):
    """Raised when webhook signature verification fails."""

    pass


class WebhookProcessingError(WebhookError):
    """Raised when webhook event processing fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        event_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, provider, event_id)
        self.original_error = original_error


class ProviderNotFoundError(WebhookError):
    """Raised when requested webhook provider is not found or not registered."""

    pass


class UnsupportedEventTypeError(WebhookError):
    """Raised when webhook provider doesn't support the given event type."""

    pass
