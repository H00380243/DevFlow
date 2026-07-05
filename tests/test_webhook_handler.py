"""Tests for WebhookHandler — IM Webhook Handler."""

import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


class TestWebhookHandler:
    """Test cases for WebhookHandler.handle_webhook."""

    def test_handle_webhook_requirement_message_recognized(self):
        """Test A: Given user sends plain text '加一个登录页',
        when system receives, then recognizes as requirement message."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_001",
            "sender_id": "user_001",
            "content": "加一个登录页",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "需求已提交" in result.message

    def test_handle_webhook_command_message_recognized(self):
        """Test B: Given user sends '确认 REQ-20260704-001',
        when system receives, then recognizes as command message."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_002",
            "sender_id": "user_001",
            "content": "确认 REQ-20260704-001",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "指令已执行" in result.message

    def test_handle_webhook_unsupported_message_type(self):
        """Test C: Given user sends non-text message (image/file/voice),
        when system receives, then replies with unsupported message."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_003",
            "sender_id": "user_001",
            "content": None,
            "timestamp": "2026-07-05T10:00:00Z",
            "message_type": "image",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "本轮仅支持文本需求与指令" in result.message

    def test_handle_webhook_downstream_failure_retry(self):
        """Test D: Given message reception fails,
        when system processes, then records error and retries."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_004",
            "sender_id": "user_001",
            "content": "加一个登录页",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        with patch.object(handler, '_message_router') as mock_router:
            mock_router.route.side_effect = ConnectionError("DB connection failed")
            result = handler.handle_webhook("feishu", payload)
            
            assert result.status == "error"
            assert "处理失败" in result.message

    def test_handle_webhook_empty_content(self):
        """Test E: Given post with content='' (empty string),
        when system receives, then returns unsupported."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_005",
            "sender_id": "user_001",
            "content": "",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "本轮仅支持文本需求与指令" in result.message

    def test_handle_webhook_max_length_content(self):
        """Test F: Given post with content of 10,000 chars (max boundary),
        when system receives, then processes normally."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_006",
            "sender_id": "user_001",
            "content": "a" * 10000,
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "需求已提交" in result.message

    def test_handle_webhook_missing_required_field(self):
        """Test G: Given post with payload missing sender_id field,
        when system receives, then returns 400 error."""
        from app.core.webhook import WebhookHandler, WebhookValidationError
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_007",
            "content": "加一个登录页",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        with pytest.raises(WebhookValidationError) as exc_info:
            handler.handle_webhook("feishu", payload)
        
        assert "missing required field" in str(exc_info.value).lower()

    def test_handle_webhook_sql_injection_content(self):
        """Test H: Given post with content="'; DROP TABLE requirements; --"
        (SQL injection), when system receives, then content stored as literal."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_008",
            "sender_id": "user_001",
            "content": "'; DROP TABLE requirements; --",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "需求已提交" in result.message

    def test_handle_webhook_xss_content(self):
        """Test I: Given post with content="<script>alert('xss')</script>"
        (XSS), when system receives, then content stored as literal."""
        from app.core.webhook import WebhookHandler
        
        handler = WebhookHandler()
        payload = {
            "message_id": "msg_009",
            "sender_id": "user_001",
            "content": "<script>alert('xss')</script>",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        result = handler.handle_webhook("feishu", payload)
        
        assert result.status == "ok"
        assert "需求已提交" in result.message

    def test_handle_webhook_valid_c001_schema(self):
        """Test J: Given post to /webhook/im/feishu with valid IM Webhook Payload JSON,
        when system receives, then returns C-001 response schema."""
        from app.main import create_app
        
        app = create_app()
        client = TestClient(app)
        
        payload = {
            "message_id": "msg_010",
            "sender_id": "user_001",
            "content": "加一个登录页",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        response = client.post("/webhook/im/feishu", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data

    def test_handle_webhook_malformed_json(self):
        """Test K: Given post to /webhook/im/feishu with malformed JSON body,
        when system receives, then returns 422 error (FastAPI validation)."""
        from app.main import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.post(
            "/webhook/im/feishu",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == 422

    def test_handle_webhook_concurrent_performance(self):
        """Test L: Given 100 concurrent POST requests to /webhook/im/feishu,
        when system processes, then P95 response time < 5s."""
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        from app.main import create_app
        
        app = create_app()
        client = TestClient(app)
        
        payload = {
            "message_id": "msg_{i}",
            "sender_id": "user_001",
            "content": "加一个登录页",
            "timestamp": "2026-07-05T10:00:00Z",
        }
        
        def make_request(i):
            start = time.time()
            response = client.post("/webhook/im/feishu", json=payload)
            return time.time() - start
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            durations = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        durations.sort()
        p95_index = int(len(durations) * 0.95)
        p95_time = durations[p95_index]
        
        assert p95_time < 5.0, f"P95 response time {p95_time}s exceeds 5s threshold"