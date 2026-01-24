"""MongoDB model helpers for video parts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from typing_extensions import Annotated

from pydantic import BaseModel, Field, StringConstraints, constr

# This file contains the model for the video_parts for video (that it will be composed of)
# It should be contain following data points
# video_parts_id (integer)
# custom video_id (VARCHAR)
# file_part_name
# video_size
# total_duration
# selected_duration
# modification_time
# active (BOOLEAN)
# creation_time

VIDEO_PARTS_COLLECTION = "video_parts"


@dataclass
class VideoPartModel:
    video_parts_id: Optional[str]
    video_id: str
    file_part_name: str
    part_number: int
    file_location: str
    file_duration: str
    start_time: str
    end_time: str
    video_size: Optional[str] = None
    total_duration: Optional[float] = None
    selected_duration: Optional[float] = None
    modification_time: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    creation_time: datetime = field(default_factory=datetime.utcnow)

    def to_bson(self) -> Dict[str, Any]:
        return {
            "video_parts_id": self.video_parts_id,
            "video_id": self.video_id,
            "file_part_name": self.file_part_name,
            "part_number": self.part_number,
            "file_location": self.file_location,
            "file_duration": self.file_duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "video_size": self.video_size,
            "total_duration": self.total_duration,
            "selected_duration": self.selected_duration,
            "modification_time": self.modification_time,
            "active": self.active,
            "creation_time": self.creation_time,
        }

    @classmethod
    def from_bson(cls, doc: Dict[str, Any]) -> "VideoPartModel":
        return cls(
            video_parts_id=doc.get("video_parts_id", 0),
            video_id=doc.get("video_id", ""),
            file_part_name=doc.get("file_part_name", ""),
            part_number=doc.get("part_number", 0),
            file_location=doc.get("file_location", ""),
            file_duration=doc.get("file_duration", ""),
            start_time=doc.get("start_time", ""),
            end_time=doc.get("end_time", ""),
            video_size=doc.get("video_size"),
            total_duration=doc.get("total_duration"),
            selected_duration=doc.get("selected_duration"),
            modification_time=doc.get("modification_time", datetime.utcnow()),
            active=doc.get("active", True),
            creation_time=doc.get("creation_time", datetime.utcnow()),
        )


class VideoPartSchema(BaseModel):
    video_parts_id: Optional[str]
    video_id: str
    file_part_name: str
    part_number: int
    file_location: str
    file_duration: str
    start_time: str
    end_time: str
    video_size: Optional[str] = None
    total_duration: Optional[float] = None
    selected_duration: Optional[float] = None
    modification_time: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
    creation_time: datetime = Field(default_factory=datetime.utcnow)


class VideoPartCreate(BaseModel):
    video_parts_id: Optional[str] = None
    video_id: constr(strip_whitespace=True, min_length=1)
    file_part_name: constr(strip_whitespace=True, min_length=1)
    part_number: int
    file_location: constr(strip_whitespace=True, min_length=1)
    start_time: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^\d{2}:\d{2}:\d{2}$"),
    ]
    end_time: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^\d{2}:\d{2}:\d{2}$"),
    ]
    video_size: Optional[str] = None
    total_duration: Optional[float] = None
    selected_duration: Optional[float] = None
    active: Optional[bool] = None


class VideoPartUpdate(BaseModel):
    part_number: int
    file_part_name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    file_location: Optional[constr(strip_whitespace=True, min_length=1)] = None
    start_time: Optional[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, min_length=1, pattern=r"^\d{2}:\d{2}:\d{2}$"
            ),
        ]
    ] = None
    end_time: Optional[
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, min_length=1, pattern=r"^\d{2}:\d{2}:\d{2}$"
            ),
        ]
    ] = None
    video_size: Optional[str] = None
    total_duration: Optional[float] = None
    selected_duration: Optional[float] = None
    active: Optional[bool] = None
