"""MongoDB model helpers for voice clone job status."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, constr

VOICE_CLONE_JOB_COLLECTION = "voice_clone_job"

VoiceCloneJobStatus = Literal["queued", "processing", "completed", "failed"]


def _now_utc() -> datetime:
    return datetime.utcnow()


@dataclass
class VoiceCloneJobModel:
    job_id: str
    ref_audio_path: str
    ref_text: str
    status: VoiceCloneJobStatus = "queued"
    progress: Optional[float] = None
    result_path: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime = field(default_factory=_now_utc)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=_now_utc)

    def to_bson(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "ref_audio_path": self.ref_audio_path,
            "ref_text": self.ref_text,
            "status": self.status,
            "progress": self.progress,
            "result_path": self.result_path,
            "error_reason": self.error_reason,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_bson(cls, doc: Dict[str, Any]) -> "VoiceCloneJobModel":
        return cls(
            job_id=doc.get("job_id", ""),
            ref_audio_path=doc.get("ref_audio_path", ""),
            ref_text=doc.get("ref_text", ""),
            status=doc.get("status", "queued"),
            progress=doc.get("progress"),
            result_path=doc.get("result_path"),
            error_reason=doc.get("error_reason"),
            created_at=doc.get("created_at", _now_utc()),
            started_at=doc.get("started_at"),
            completed_at=doc.get("completed_at"),
            updated_at=doc.get("updated_at", _now_utc()),
        )


class VoiceCloneJobSchema(BaseModel):
    job_id: str
    ref_audio_path: str
    ref_text: str
    status: VoiceCloneJobStatus = "queued"
    progress: Optional[float] = None
    result_path: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=_now_utc)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=_now_utc)


class VoiceCloneJobCreate(BaseModel):
    job_id: constr(strip_whitespace=True, min_length=1)
    ref_audio_path: constr(strip_whitespace=True, min_length=1)
    ref_text: constr(strip_whitespace=True, min_length=1)
    status: Optional[VoiceCloneJobStatus] = None
    progress: Optional[float] = None
    result_path: Optional[str] = None
    error_reason: Optional[str] = None


class VoiceCloneJobUpdate(BaseModel):
    status: Optional[VoiceCloneJobStatus] = None
    progress: Optional[float] = None
    result_path: Optional[str] = None
    error_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
