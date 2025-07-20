"""
Security utilities for webhook signature verification.
"""

import hashlib
import hmac
import logging
from typing import Dict

from src.webhooks.shared.exceptions import WebhookSignatureError

logger = logging.getLogger(__name__)


class WebhookSignatureValidator:
    """Utility class for validating webhook signatures."""

    @staticmethod
    def validate_hmac_sha256(
        payload: bytes,
        signature: str,
        secret: str,
        signature_header_format: str = "sha256={signature}",
    ) -> bool:
        """
        Validate HMAC SHA256 signature.

        Args:
            payload: Raw webhook payload bytes
            signature: Signature from webhook headers
            secret: Webhook secret key
            signature_header_format: Format of signature header (default: "sha256={signature}")

        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning(
                "No webhook secret provided - skipping signature verification"
            )
            return True

        if not signature:
            logger.warning("No signature header found")
            return False

        # Extract signature hash from header format
        expected_prefix = signature_header_format.split("{signature}")[0]
        if not signature.startswith(expected_prefix):
            logger.warning(
                f"Invalid signature format. Expected prefix: {expected_prefix}"
            )
            return False

        received_signature = signature[len(expected_prefix) :]

        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

        # Use secure comparison
        is_valid = hmac.compare_digest(received_signature, expected_signature)

        if not is_valid:
            logger.warning("Webhook signature verification failed")

        return is_valid

    @staticmethod
    def validate_clickup_signature(
        payload: bytes, headers: Dict[str, str], secret: str
    ) -> bool:
        """
        Validate ClickUp webhook signature.

        Args:
            payload: Raw webhook payload
            headers: Request headers
            secret: ClickUp webhook secret

        Returns:
            True if signature is valid

        Raises:
            WebhookSignatureError: If signature validation fails
        """
        signature = headers.get("x-signature", "")

        try:
            return WebhookSignatureValidator.validate_hmac_sha256(
                payload=payload,
                signature=signature,
                secret=secret,
                signature_header_format="sha256={signature}",
            )
        except Exception as e:
            raise WebhookSignatureError(
                f"ClickUp signature validation failed: {e}", provider="clickup"
            )

    @staticmethod
    def validate_discord_signature(
        payload: bytes, headers: Dict[str, str], secret: str
    ) -> bool:
        """
        Validate Discord webhook signature.

        Args:
            payload: Raw webhook payload
            headers: Request headers
            secret: Discord webhook secret

        Returns:
            True if signature is valid

        Raises:
            WebhookSignatureError: If signature validation fails
        """
        # Discord uses different signature format
        signature = headers.get("x-signature-ed25519", "")
        timestamp = headers.get("x-signature-timestamp", "")

        # Discord signature validation would be implemented here
        # For now, just validate the presence of required headers
        if not signature or not timestamp:
            raise WebhookSignatureError(
                "Missing Discord signature headers", provider="discord"
            )

        # TODO: Implement actual Discord signature validation
        # Discord uses Ed25519 signatures, not HMAC
        logger.warning("Discord signature validation not yet implemented")
        return True

    @staticmethod
    def validate_github_signature(
        payload: bytes, headers: Dict[str, str], secret: str
    ) -> bool:
        """
        Validate GitHub webhook signature.

        Args:
            payload: Raw webhook payload
            headers: Request headers
            secret: GitHub webhook secret

        Returns:
            True if signature is valid

        Raises:
            WebhookSignatureError: If signature validation fails
        """
        signature = headers.get("x-hub-signature-256", "")

        try:
            return WebhookSignatureValidator.validate_hmac_sha256(
                payload=payload,
                signature=signature,
                secret=secret,
                signature_header_format="sha256={signature}",
            )
        except Exception as e:
            raise WebhookSignatureError(
                f"GitHub signature validation failed: {e}", provider="github"
            )
