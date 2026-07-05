"""Message Router for IM Webhook Handler."""

import re
from datetime import datetime

from app.models import IMMessage, MessageType, MessageResult


class MessageRouterError(Exception):
    """Raised when message routing fails."""
    pass


# Consolidated command pattern regex
COMMAND_PATTERN = re.compile(
    r"^(确认|驳回|进度)\s+REQ-\d{8}-\d{3}|我的列表$"
)


class MessageRouter:
    """Routes IM messages based on content type and pattern matching."""

    def route(self, message: IMMessage) -> MessageResult:
        """Route an IM message to the appropriate handler.

        Args:
            message: The IM message to route.

        Returns:
            MessageResult with status and message fields.

        Raises:
            MessageRouterError: When routing fails.
        """
        try:
            message_type = self._identify_type(message)

            if message_type == MessageType.REQUIREMENT:
                # Generate requirement ID (simplified for now)
                req_id = self._generate_requirement_id()
                return MessageResult(
                    status="ok",
                    message=f"需求已提交：{req_id}"
                )
            elif message_type == MessageType.COMMAND:
                return MessageResult(
                    status="ok",
                    message="指令已执行"
                )
            else:
                return MessageResult(
                    status="ok",
                    message="本轮仅支持文本需求与指令"
                )
        except Exception as e:
            raise MessageRouterError(f"Routing failed: {e}") from e

    def _identify_type(self, message: IMMessage) -> MessageType:
        """Identify the type of an IM message.

        Args:
            message: The IM message to classify.

        Returns:
            MessageType enum value.
        """
        # Check content type
        if message.message_type != MessageType.TEXT:
            return MessageType.UNSUPPORTED

        # Check if content is empty
        if not message.content or message.content.strip() == "":
            return MessageType.UNSUPPORTED

        # Check command pattern
        if COMMAND_PATTERN.match(message.content):
            return MessageType.COMMAND

        # Default to requirement
        return MessageType.REQUIREMENT

    def _generate_requirement_id(self) -> str:
        """Generate a requirement ID in format REQ-YYYYMMDD-NNN.

        Returns:
            Generated requirement ID.
        """
        today = datetime.now().strftime("%Y%m%d")
        # Simplified: use a counter (in real implementation, this would be from DB)
        counter = 1
        return f"REQ-{today}-{counter:03d}"