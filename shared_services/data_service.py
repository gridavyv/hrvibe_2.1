# TAGS: [status_validation], [get_data], [create_data], [update_data], [directory_path], [file_path], [persistent_keyboard], [format_data]

import os
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Type

# Add project root to path to access shared_services
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

from shared_services.constants import (
    USERS_RECORDS_FILENAME, 
    RESUME_RECORDS_FILENAME,
    BOT_FOR_APPLICANTS_USERNAME,
    )
from shared_services.db_service import get_column_value_in_db
from database import Base


def create_json_file_with_dictionary_content(file_path: Path, content_to_write: dict) -> None:
    # TAGS: [create_data],[file_path]
    """Create a JSON file from a dictionary.
    If file already exists, it will be overwritten."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(content_to_write, f, ensure_ascii=False, indent=2)
    logger.debug(f"Content written to {file_path}")


def get_employer_id_from_json_value_from_db(db_model: Type[Base], record_id: str) -> Optional[str]:
    """Get employer id from JSON value from database. TAGS: [get_data]"""
    hh_data = get_column_value_in_db(db_model, record_id, "hh_data")
    if not isinstance(hh_data, dict):
        logger.debug(f"'record_id': {record_id} not found in DB or hh_data is empty")
        return None

    employer_id = hh_data.get("employer", {}).get("id")
    if employer_id:
        logger.debug(f"'employer_id': {employer_id} found for 'bot_user_id': {record_id} in DB")
        return employer_id

    logger.debug(f"'employer_id' not found in hh_data for 'bot_user_id': {record_id}")
    return None