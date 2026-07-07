"""Design Output Handler — F013 设计产出物生成.

Generates structured design document, uploads to storage, validates interfaces,
transitions state, and notifies submitter after design team completes.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.state_machine import Event, RequirementNotFoundError, StateMachine
from app.models import DesignResults, Requirements

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class UploadFailedError(Exception):
    def __init__(self, filename: str, message: str):
        self.filename = filename
        self.message = message
        super().__init__(f"设计文档上传失败: {filename} — {message}")


class DesignOutputHandler:
    def __init__(
        self,
        session: Session,
        upload_fn: Callable[[str, str], str],
        push_fn: Callable[[str, str], None],
    ):
        self._session = session
        self._upload_fn = upload_fn
        self._push_fn = push_fn
        self._sm = StateMachine(session)

    def complete_design(self, req_id: str) -> str:
        req = self._session.query(Requirements).filter(Requirements.id == req_id).first()
        if req is None:
            raise RequirementNotFoundError(req_id)

        max_version = (
            self._session.query(func.max(DesignResults.version))
            .filter(DesignResults.requirement_id == req_id)
            .scalar()
        )
        if max_version is None:
            raise RequirementNotFoundError(f"No design outputs for {req_id}")

        outputs = (
            self._session.query(DesignResults)
            .filter(
                DesignResults.requirement_id == req_id,
                DesignResults.version == max_version,
            )
            .all()
        )

        doc_content = self._generate_document(req_id, max_version, outputs)
        filename = f"design/{req_id}/v{max_version}.json"

        try:
            document_url = self.upload_document(doc_content, filename)
        except UploadFailedError as e:
            self._push_fn("admin", f"设计文档上传失败: {req_id} — {e.message}")
            raise

        design_row = (
            self._session.query(DesignResults)
            .filter(
                DesignResults.requirement_id == req_id,
                DesignResults.version == max_version,
                DesignResults.agent_role == "产品设计",
            )
            .first()
        )
        if design_row is not None:
            design_row.document_url = document_url
            self._session.commit()

        self._sm.transition(req_id, Event.DESIGN_COMPLETE, trigger_user=None)

        self._push_fn(
            req.submitter_id,
            f"设计完成 [{req_id}] 查看详情: {document_url}",
        )

        return document_url

    def upload_document(self, content: str, filename: str) -> str:
        if not content:
            raise UploadFailedError(filename, "empty content")
        if not filename:
            raise UploadFailedError(filename, "empty filename")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._upload_fn(content, filename)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        raise UploadFailedError(filename, str(last_error))

    def _validate_interfaces(
        self, interfaces: list[dict], req_text: str
    ) -> list[dict]:
        result: list[dict] = []
        for iface in interfaces:
            method = iface.get("method", "")
            signature = iface.get("signature", "")
            is_confirmed = (method in req_text) and bool(signature)
            enhanced = dict(iface)
            enhanced["is_confirmed"] = is_confirmed
            result.append(enhanced)
        return result

    def _generate_document(
        self, req_id: str, version: int, outputs: list[DesignResults]
    ) -> str:
        design_content = ""
        user_flow = "参见设计文档"
        skeleton_dirs: list[str] = []
        core_interfaces_raw: list[dict] = []
        risk_warnings: list[str] = []
        recommendations = "参见设计文档"
        has_high_risk = False

        for output in outputs:
            if output.agent_role == "产品设计":
                design_content = output.document_url or ""
            elif output.agent_role == "技术选型":
                skeleton_dirs = output.skeleton_dirs or []
                core_interfaces_raw = output.core_interfaces or []
            elif output.agent_role == "合规风控":
                risk_warnings = output.risk_warnings or []
                has_high_risk = any("[高风险]" in (w or "") for w in risk_warnings)

        core_interfaces_validated = self._validate_interfaces(
            core_interfaces_raw, design_content
        )

        doc = {
            "requirement_id": req_id,
            "version": version,
            "design_content": design_content,
            "user_flow": user_flow,
            "skeleton_dirs": skeleton_dirs,
            "core_interfaces": core_interfaces_validated,
            "risk_warnings": risk_warnings,
            "recommendations": recommendations,
            "has_high_risk": has_high_risk,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return json.dumps(doc, ensure_ascii=False, indent=2)
