"""MongoDB model helpers for person bios."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, constr

PERSON_BIO_COLLECTION = "person_bio"
_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _now_str() -> str:
    return datetime.utcnow().strftime(_DATETIME_FORMAT)


@dataclass
class PersonBioModel:
    code: str
    name: str
    country: str
    dob: str
    excellence_field: str
    challenges: str
    added_on: str = field(default_factory=_now_str)
    updated_on: str = field(default_factory=_now_str)

    def to_bson(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "country": self.country,
            "dob": self.dob,
            "excellence_field": self.excellence_field,
            "challenges": self.challenges,
            "added_on": self.added_on,
            "updated_on": self.updated_on,
        }

    @classmethod
    def from_bson(cls, doc: Dict[str, Any]) -> "PersonBioModel":
        return cls(
            code=doc.get("code", ""),
            name=doc.get("name", ""),
            country=doc.get("country", ""),
            dob=doc.get("dob", ""),
            excellence_field=doc.get("excellence_field", ""),
            challenges=doc.get("challenges", ""),
            added_on=doc.get("added_on", _now_str()),
            updated_on=doc.get("updated_on", _now_str()),
        )


class PersonBioSchema(BaseModel):
    code: str
    name: str
    country: str
    dob: str
    excellence_field: str
    challenges: str
    added_on: str
    updated_on: str


class PersonBioResponse(BaseModel):
    id: str = Field(..., alias="_id")
    code: str
    name: str
    country: str
    dob: str
    excellence_field: str
    challenges: str
    added_on: str
    updated_on: str

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class PersonBioCreate(BaseModel):
    code: constr(strip_whitespace=True, min_length=1)
    name: constr(strip_whitespace=True, min_length=1)
    country: constr(strip_whitespace=True, min_length=1)
    dob: constr(strip_whitespace=True, min_length=1)
    excellence_field: constr(strip_whitespace=True, min_length=1)
    challenges: constr(strip_whitespace=True, min_length=1)


class PersonBioUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    country: Optional[constr(strip_whitespace=True, min_length=1)] = None
    dob: Optional[constr(strip_whitespace=True, min_length=1)] = None
    excellence_field: Optional[constr(strip_whitespace=True, min_length=1)] = None
    challenges: Optional[constr(strip_whitespace=True, min_length=1)] = None
    updated_on: Optional[str] = None
