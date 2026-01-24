"""Shared configuration for video processing."""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

OUTPUT_FOLDER = os.getenv("OUTPUT_FILES_LOCATION") or "./outputs"
INPUT_FOLDER = os.getenv("INPUT_FILES_LOCATION", "")

if OUTPUT_FOLDER and not OUTPUT_FOLDER.endswith(os.sep):
    OUTPUT_FOLDER += os.sep
if INPUT_FOLDER and not INPUT_FOLDER.endswith(os.sep):
    INPUT_FOLDER += os.sep
