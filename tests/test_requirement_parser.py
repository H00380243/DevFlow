"""Tests for RequirementParser — F004 需求结构化与 ID 生成."""

import re
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.core.requirement_parser import (
    RequirementParseError,
    RequirementParser,
    IdGenerationError,
)
from app.models import IMMessage, StructuredRequirement


class TestParseValidRequirement:
    """Test A: Basic happy path — parse valid requirement."""

    def test_parse_valid_generates_id(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_001",
            sender_id="user1",
            content="加一个登录页",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-001"):
            result = parser.parse(msg)

        assert isinstance(result, StructuredRequirement)
        assert result.id == "REQ-20260705-001"
        assert result.original_text == "加一个登录页"
        assert result.summary == "加一个登录页"
        assert result.submitter_id == "user1"
        assert result.tags == []
        assert result.created_at is not None

    def test_parse_sets_submitter_name_none(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_002",
            sender_id="user1",
            content="加一个登录页",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-001"):
            result = parser.parse(msg)

        assert result.submitter_name is None


class TestParseExtractsIntentAndConstraints:
    """Test B: Parse extracts intent and constraint keywords."""

    def test_parse_extracts_tags_and_constraints(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_003",
            sender_id="user2",
            content="实现用户管理模块，必须支持RBAC权限",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-002"):
            result = parser.parse(msg)

        assert result.summary != ""
        assert result.summary is not None
        assert result.id == "REQ-20260705-002"
        assert isinstance(result.tags, list)


class TestParseNullContent:
    """Test C: FR-002 AC-2 — null content raises error."""

    def test_parse_null_content_raises(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_004",
            sender_id="user1",
            content=None,
            timestamp="2026-07-05T10:00:00Z",
        )

        with pytest.raises(RequirementParseError, match="需求文本不能为空"):
            parser.parse(msg)


class TestParseEmptyContent:
    """Test D: FR-002 AC-2 — empty content raises error."""

    def test_parse_empty_content_raises(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_005",
            sender_id="user1",
            content="",
            timestamp="2026-07-05T10:00:00Z",
        )

        with pytest.raises(RequirementParseError, match="需求文本不能为空"):
            parser.parse(msg)

    def test_parse_whitespace_only_content_raises(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_005b",
            sender_id="user1",
            content="   ",
            timestamp="2026-07-05T10:00:00Z",
        )

        with pytest.raises(RequirementParseError, match="需求文本不能为空"):
            parser.parse(msg)


class TestParseUnparseableContent:
    """Test E: FR-002 AC-3 — unparseable text still generates entry."""

    def test_parse_unparseable_marks_pending(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_006",
            sender_id="user1",
            content="!!!@@@###",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-003"):
            result = parser.parse(msg)

        assert result.id == "REQ-20260705-003"
        assert result.original_text == "!!!@@@###"


class TestGenerateIdBelow999:
    """Test F: FR-002 AC-4 — boundary: max_seq=998 → 3-digit."""

    def test_generate_id_3digit_below_999(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 998
        mock_session.execute.return_value = mock_result

        parser = RequirementParser(db_session=mock_session)
        with patch("app.core.requirement_parser.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = parser.generate_id()

        assert result == "REQ-20260705-999"


class TestGenerateIdAt999Expands:
    """Test G: FR-002 AC-4 — max_seq=999 → 4-digit expansion."""

    def test_generate_id_expands_to_4digit(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 999
        mock_session.execute.return_value = mock_result

        parser = RequirementParser(db_session=mock_session)
        with patch("app.core.requirement_parser.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = parser.generate_id()

        assert result == "REQ-20260705-1000"


class TestGenerateIdAt9999Raises:
    """Test H: FR-002 AC-4 — max_seq=9999 → exhaustion error."""

    def test_generate_id_raises_on_exhaustion(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 9999
        mock_session.execute.return_value = mock_result

        parser = RequirementParser(db_session=mock_session)
        with patch("app.core.requirement_parser.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            with pytest.raises(IdGenerationError, match="Sequence exhausted"):
                parser.generate_id()


class TestGenerateIdFirstOfDay:
    """Test I: NULL max_seq → first request starts at 001."""

    def test_generate_id_first_of_day(self):
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        parser = RequirementParser(db_session=mock_session)
        with patch("app.core.requirement_parser.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = parser.generate_id()

        assert result == "REQ-20260705-001"


class TestGenerateIdDbFailure:
    """Test N: DB query failure raises IdGenerationError."""

    def test_generate_id_db_failure_raises(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError("db", {}, Exception("fail"))

        parser = RequirementParser(db_session=mock_session)
        with pytest.raises(IdGenerationError, match="Failed to query sequence counter"):
            parser.generate_id()


class TestExtractIntentFirstSentence:
    """Test Q: _extract_intent returns first sentence."""

    def test_extract_intent_first_sentence(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_intent("第一个句子。第二个句子。")
        assert result == "第一个句子"

    def test_extract_intent_single_sentence(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_intent("这是一个需求")
        assert result == "这是一个需求"

    def test_extract_intent_with_exclamation(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_intent("需要登录功能！其他功能后续再说")
        assert result == "需要登录功能"

    def test_extract_intent_empty_string(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_intent("")
        assert result == ""

    def test_extract_intent_truncates_long(self):
        parser = RequirementParser(db_session=MagicMock())
        long_text = "a" * 300
        result = parser._extract_intent(long_text)
        assert len(result) <= 200

    def test_extract_intent_only_delimiters_returns_stripped(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_intent("。。。\n\n")
        assert result == "。。。"


class TestExtractConstraints:
    """Test R, S: _extract_constraints filters keywords."""

    def test_extract_constraints_filters_keywords(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_constraints("必须支持RBAC。可以使用JWT。")
        assert result == ["必须支持RBAC"]

    def test_extract_constraints_no_keywords_empty_list(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_constraints("随便写点什么")
        assert result == []

    def test_extract_constraints_multiple(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_constraints("必须登录。不能超过10人。需要加密。")
        assert len(result) == 3

    def test_extract_constraints_empty(self):
        parser = RequirementParser(db_session=MagicMock())
        result = parser._extract_constraints("")
        assert result == []


class TestConcurrentIdGeneration:
    """Test T: INTG — concurrent generate_id calls produce unique IDs."""

    def test_concurrent_generate_id_unique(self):
        from datetime import datetime
        mock_session = MagicMock()
        # Simulate: first call returns None (empty DB), second returns 1
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.scalar.return_value = None
            else:
                mock_result.scalar.return_value = 1
            return mock_result

        mock_session.execute.side_effect = side_effect
        parser = RequirementParser(db_session=mock_session)

        id1 = parser.generate_id()
        id2 = parser.generate_id()
        today = datetime.now().strftime("%Y%m%d")

        assert id1 != id2
        assert id1 == f"REQ-{today}-001"
        assert id2 == f"REQ-{today}-002"


class TestParseSqlInjection:
    """Test V: SEC — SQL injection content is stored as literal string."""

    def test_parse_sql_injection_content(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_010",
            sender_id="user1",
            content="'; DROP TABLE requirements; --",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-010"):
            result = parser.parse(msg)

        assert result.id == "REQ-20260705-010"
        assert result.original_text == "'; DROP TABLE requirements; --"
        assert result.summary == "'; DROP TABLE requirements; --"


class TestParseXssContent:
    """Test W: SEC — XSS content stored as literal string."""

    def test_parse_xss_content(self):
        parser = RequirementParser(db_session=MagicMock())
        msg = IMMessage(
            message_id="msg_011",
            sender_id="user1",
            content="<script>alert(1)</script>",
            timestamp="2026-07-05T10:00:00Z",
        )
        with patch.object(parser, "generate_id", return_value="REQ-20260705-011"):
            result = parser.parse(msg)

        assert result.id == "REQ-20260705-011"
        assert result.original_text == "<script>alert(1)</script>"


class TestStructuredRequirementModel:
    """Test StructuredRequirement Pydantic model validation."""

    def test_structured_requirement_defaults(self):
        sr = StructuredRequirement(
            id="REQ-20260705-001",
            original_text="test",
            summary="test",
            submitter_id="user1",
        )
        assert sr.tags == []
        assert sr.submitter_name is None
        assert sr.estimated_scope is None
        assert sr.created_at is not None

    def test_structured_requirement_with_tags(self):
        sr = StructuredRequirement(
            id="REQ-20260705-001",
            original_text="test",
            summary="test",
            submitter_id="user1",
            tags=["login", "auth"],
        )
        assert sr.tags == ["login", "auth"]
