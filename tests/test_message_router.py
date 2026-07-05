"""Tests for MessageRouter — IM Message Router."""

import pytest
from app.core.message_router import MessageRouter, MessageType, MessageResult
from app.models import IMMessage


class TestMessageRouter:
    """Test cases for MessageRouter."""

    def test_identify_type_requirement(self):
        """Test plain text message is identified as REQUIREMENT."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_001",
            sender_id="user_001",
            content="加一个登录页",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.REQUIREMENT

    def test_identify_type_command_confirm(self):
        """Test command pattern '确认 REQ-xxx' is identified as COMMAND."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_002",
            sender_id="user_001",
            content="确认 REQ-20260704-001",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.COMMAND

    def test_identify_type_command_reject(self):
        """Test command pattern '驳回 REQ-xxx' is identified as COMMAND."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_003",
            sender_id="user_001",
            content="驳回 REQ-20260704-001 修改意见XXX",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.COMMAND

    def test_identify_type_command_progress(self):
        """Test command pattern '进度 REQ-xxx' is identified as COMMAND."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_004",
            sender_id="user_001",
            content="进度 REQ-20260704-001",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.COMMAND

    def test_identify_type_command_list(self):
        """Test command pattern '我的列表' is identified as COMMAND."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_005",
            sender_id="user_001",
            content="我的列表",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.COMMAND

    def test_identify_type_unsupported_image(self):
        """Test image message type is identified as UNSUPPORTED."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_006",
            sender_id="user_001",
            content=None,
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.IMAGE,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.UNSUPPORTED

    def test_identify_type_unsupported_empty_content(self):
        """Test empty content is identified as UNSUPPORTED."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_007",
            sender_id="user_001",
            content="",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router._identify_type(message)
        
        assert result == MessageType.UNSUPPORTED

    def test_route_requirement_message(self):
        """Test routing requirement message returns correct result."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_008",
            sender_id="user_001",
            content="加一个登录页",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router.route(message)
        
        assert isinstance(result, MessageResult)
        assert result.status == "ok"
        assert "需求已提交" in result.message

    def test_route_command_message(self):
        """Test routing command message returns correct result."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_009",
            sender_id="user_001",
            content="确认 REQ-20260704-001",
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.TEXT,
        )
        
        result = router.route(message)
        
        assert isinstance(result, MessageResult)
        assert result.status == "ok"
        assert "指令已执行" in result.message

    def test_route_unsupported_message(self):
        """Test routing unsupported message returns correct result."""
        router = MessageRouter()
        message = IMMessage(
            message_id="msg_010",
            sender_id="user_001",
            content=None,
            timestamp="2026-07-05T10:00:00Z",
            message_type=MessageType.IMAGE,
        )
        
        result = router.route(message)
        
        assert isinstance(result, MessageResult)
        assert result.status == "ok"
        assert "本轮仅支持文本需求与指令" in result.message