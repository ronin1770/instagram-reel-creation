"""Prompt name constants and mappings for the backend."""

from __future__ import annotations

from typing import Dict, List

MONTHLY_FIGURES = "monthly_figures.txt"
BIO_DETAILS = "bio_details.txt"
QUOTES = "quotes.txt"

AI_TYPE_PROMPT_MAP: Dict[str, str] = {
    "MONTHLY_FIGURES": MONTHLY_FIGURES,
    "BIO_DETAILS": BIO_DETAILS,
    "QUOTES": QUOTES,
}

AI_TYPE_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "MONTHLY_FIGURES": ["given_month", "field_of_excellence"],
    "BIO_DETAILS": [
        "code",
        "person_name",
        "country",
        "dob",
        "fields_of_excellent",
        "summary_of_challenges",
    ],
    "QUOTES": [
        "code",
        "person_name",
        "country",
        "dob",
        "field_of_excellence",
    ],
}

AI_TYPE_VARIABLE_MAP: Dict[str, Dict[str, str]] = {
    "MONTHLY_FIGURES": {
        "given_month": "GIVEN_MONTH",
        "field_of_excellence": "FIELD_OF_EXCELLENCE",
    },
    "BIO_DETAILS": {
        "code": "CODE",
        "person_name": "PERSON_NAME",
        "country": "COUNTRY",
        "dob": "DOB",
        "fields_of_excellent": "Fields_OF_EXCELLENCE",
        "summary_of_challenges": "SUMMARY_OF_CHALLENGES",
    },
    "QUOTES": {
        "code": "CODE",
        "person_name": "PERSON_NAME",
        "country": "COUNTRY",
        "dob": "DOB",
        "field_of_excellence": "Fields_OF_EXCELLENCE",
    },
}

AI_TYPES = sorted(AI_TYPE_PROMPT_MAP.keys())
