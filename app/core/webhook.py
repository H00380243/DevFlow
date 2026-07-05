"""Webhook Handler for IM Integration."""

import json
import logging
from typing import Any

from app.core.message_router import MessageRouter, MessageRouterError
from app.models import IMMessage, MessageType, WebhookPayload, WebhookResponse

logger = logging.getLogger(__name__)

# Constants
CONFIGURED_PLATFORMS = ["feishu", "dingtalk", "wechat"]
REQUIRED_FIELDS = ["message_id", "sender_id", "content", "timestamp"]


class WebhookValidationError(Exception):
    """Raised when webhook payload validation fails."""
    pass


class WebhookProcessingError(Exception):
    """Raised when webhook processing fails after retries."""
    pass


def validate_webhook_payload(payload: dict[str, Any]) -> None:
    """Validate webhook payload has all required fields.

    Args:
        payload: Raw JSON payload from IM platform.

    Raises:
        WebhookValidationError: When payload is missing required fields.
    """
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise WebhookValidationError(f"missing required field: {field}")


class WebhookHandler:
    """Handles incoming IM webhook requests."""

    def __init__(self):
        """Initialize WebhookHandler with MessageRouter."""
        self._message_router = MessageRouter()

    def handle_webhook(self, platform: str, payload: dict[str, Any]) -> WebhookResponse:
        """Handle incoming webhook request from IM platform.

        Args:
            platform: IM platform identifier (e.g., 'feishu', 'dingtalk').
            payload: Raw JSON payload from IM platform.

        Returns:
            WebhookResponse with status and message.

        Raises:
            WebhookValidationError: When payload validation fails.
            WebhookProcessingError: When processing fails after retries.
        """
        # Validate platform is configured
        if platform not in CONFIGURED_PLATFORMS:
            raise WebhookValidationError(f"unknown platform: {platform}")

        # Validate payload fields
        validate_webhook_payload(payload)

        # Determine message type
        message_type = MessageType.TEXT
        if payload.get("message_type"):
            try:
                message_type = MessageType(payload["message_type"])
            except ValueError:
                message_type = MessageType.TEXT

        # Construct IMMessage
        message = IMMessage(
            message_id=payload["message_id"],
            sender_id=payload["sender_id"],
            content=payload.get("content"),
            timestamp=payload["timestamp"],
            message_type=message_type,
        )

        # Delegate to MessageRouter
        try:
            result = self._message_router.route(message)
            return WebhookResponse(status=result.status, message=result.message)
        except MessageRouterError as e:
            logger.error(f"Message routing failed: {e}")
            return WebhookResponse(status="error", message=f"处理失败：{e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return WebhookResponse(status="error", message=f"处理失败：{e}")