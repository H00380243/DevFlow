"""Integration: Webhook → MessageRouter → RequirementParser [Real]."""

import pytest
from app.core.webhook import WebhookHandler, WebhookValidationError
from app.core.message_router import MessageRouter


class TestWebhookToRequirement:
    """Integration: F003 Webhook → F004 MessageRouter → Requirement parse."""

    def test_webhook_requirement_flow(self):
        """Real: Webhook receives requirement message → accepted."""
        handler = WebhookHandler()
        payload = {
            "message_id": "msg001",
            "sender_id": "user001",
            "content": "我需要一个登录页面，支持邮箱和微信登录",
            "timestamp": "2026-07-09T10:00:00Z",
        }
        result = handler.handle_webhook("feishu", payload)
        assert result.status == "ok"

    def test_webhook_command_flow(self):
        """Real: Webhook receives command message → accepted."""
        handler = WebhookHandler()
        payload = {
            "message_id": "msg002",
            "sender_id": "user001",
            "content": "确认 REQ-20260709-0001",
            "timestamp": "2026-07-09T10:00:01Z",
        }
        result = handler.handle_webhook("feishu", payload)
        assert result.status == "ok"

    def test_webhook_validation_missing_fields(self):
        """Real: Missing required fields → WebhookValidationError."""
        handler = WebhookHandler()
        payload = {"sender_id": "user001", "content": "test"}
        with pytest.raises(WebhookValidationError):
            handler.handle_webhook("feishu", payload)

    def test_webhook_unsupported_platform(self):
        """Real: Unknown platform → WebhookValidationError."""
        handler = WebhookHandler()
        payload = {
            "message_id": "msg003",
            "sender_id": "user001",
            "content": "test",
            "timestamp": "2026-07-09T10:00:00Z",
        }
        with pytest.raises(WebhookValidationError, match="unknown platform"):
            handler.handle_webhook("slack", payload)

    def test_message_router_classify_requirement(self):
        """Real: MessageRouter classifies requirement text."""
        from app.models import IMMessage, MessageType
        router = MessageRouter()
        msg = IMMessage(
            message_id="msg004",
            sender_id="user001",
            content="我需要一个登录页面",
            timestamp="2026-07-09T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        result = router.route(msg)
        assert result.status == "ok"

    def test_message_router_classify_command(self):
        """Real: MessageRouter classifies confirm command."""
        from app.models import IMMessage, MessageType
        router = MessageRouter()
        msg = IMMessage(
            message_id="msg005",
            sender_id="user001",
            content="确认 REQ-20260709-0001",
            timestamp="2026-07-09T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        result = router.route(msg)
        assert result.status == "ok"
