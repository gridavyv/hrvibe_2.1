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



# ****** METHODS with TAGS: [create_data] ******

def create_data_directories() -> Path:
    # TAGS: [create_data],[directory_path]
    """Create a directory for all data."""
    data_dir = Path(os.getenv("USERS_DATA_DIR", "/users_data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    list_of_sub_directories = ["videos", "vacancy_descriptions", "vacancy_sourcing_criterias", "negotiations", "resumes"]
    for sub_directory in list_of_sub_directories:
        sub_directory_path = data_dir / sub_directory
        sub_directory_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"{sub_directory_path} created or exists.")
    logger.debug(f"{data_dir} created or exists.")
    return data_dir


def get_tg_user_data_attribute_from_update_object(update: Update, tg_user_attribute: str) -> str | int | None | bool | list | dict:
    """Collects Telegram user data from context and returns it as a dictionary. TAGS: [get_data]"""
    tg_user = update.effective_user
    if tg_user:
        tg_user_attribute_value = tg_user.__getattribute__(tg_user_attribute)
        logger.debug(f"'{tg_user_attribute}': {tg_user_attribute_value} found in update.")
        return tg_user_attribute_value 
    else:
        logger.warning(f"'{tg_user_attribute}' not found in update. CHECK CORRECTNESS OF THE ATTRIBUTE NAME")
        return None


def create_oauth_link(state: str) -> str:
    # TAGS: [create_data]
    """
    Get the OAuth link for HH.ru authentication.
    """
    hh_client_id = os.getenv("HH_CLIENT_ID")
    if not hh_client_id:
        raise ValueError("HH_CLIENT_ID is not set in environment variables")
    oauth_redirect_url = os.getenv("OAUTH_REDIRECT_URL")
    if not oauth_redirect_url:
        raise ValueError("OAUTH_REDIRECT_URL is not set in environment variables")
    auth_link = f"https://hh.ru/oauth/authorize?response_type=code&client_id={hh_client_id}&state={state}&redirect_uri={oauth_redirect_url}"
    return auth_link


def create_tg_bot_link_for_applicant(bot_user_id: str, vacancy_id: str, resume_id: str) -> str:
    """Create Telegram bot link for applicant to start the bot. TAGS: [create_data]
    When the user taps it, Telegram sends your bot /start <payload>
    The payload is read from message.from.id (Telegram user_id) and the <payload> in the same update and persist the mapping.
    Example: https://t.me/{BOT_FOR_APPLICANTS_USERNAME}?start={bot_user_id}_{vacancy_id}_{resume_id}"""
    payload = f"{bot_user_id}_{vacancy_id}_{resume_id}"
    return f"https://t.me/{BOT_FOR_APPLICANTS_USERNAME}?start={payload}"

# ****** METHODS with TAGS: [get_data] ******

def get_data_directory() -> Path:
    # TAGS: [get_data],[directory_path]
    """Get the directory path for user data."""
    data_dir = Path(os.getenv("USERS_DATA_DIR", "/users_data"))
    #return id if data_dir exists
    if data_dir.exists():
        return data_dir
    #create it and return the path if it doesn't exist
    else:
        data_dir = create_data_directories()
        return data_dir


def get_data_subdirectory_path(subdirectory_name: str) -> Path:
    # TAGS: [get_data],[directory_path]
    """Get the directory path for a subdirectory of user data."""
    allowed_subdirectories = ["videos", "vacancy_descriptions", "vacancy_sourcing_criterias", "negotiations", "resumes"]
    if subdirectory_name not in allowed_subdirectories:
        logger.error(f"Invalid subdirectory name: {subdirectory_name}")
        return None
    data_dir = get_data_directory()
    subdirectory_path = data_dir / subdirectory_name
    if subdirectory_path.exists():
        return subdirectory_path
    else:
        logger.debug(f"{subdirectory_path} does not exist.")
        return None


def get_decision_status_from_selected_callback_code(selected_callback_code: str) -> str:
    #TAGS: [get_data]
    """Extract the meaningful part of a callback code.
    Args:
        selected_callback_code (str): Selected callback code, e.g. 'action_code:value'
    Returns:
        str: The part after the last colon, or the original string if no colon is present.
    """
    if ":" in selected_callback_code:
        return selected_callback_code.split(":")[-1].strip()
    else:
        return selected_callback_code


def get_access_token_from_callback_endpoint_resp(endpoint_response: dict) -> Optional[str]:
    # TAGS: [get_data]
    """Get access token from endpoint response. TAGS: [get_data]"""
    if isinstance(endpoint_response, dict):
        # return access_token if it exists in endpoint_response, otherwise return None
        return endpoint_response.get("access_token", None)
    else:
        logger.debug(f"'endpoint_response' is not a dictionary: {endpoint_response}")
        return None


def get_expires_at_from_callback_endpoint_resp(endpoint_response: dict) -> Optional[int]:
    """Get expires_at from endpoint response. TAGS: [get_data]"""
    if isinstance(endpoint_response, dict):
        return endpoint_response.get("expires_at", None)
    else:
        logger.debug(f"'endpoint_response' is not a dictionary: {endpoint_response}")
        return None

def get_reply_from_update_object(update: Update):
    """ Get user reply to from the update object if user did one of below. TAGS: [get_data].
    1. sent message (text, photo, video, etc.) - update.message OR
    2. clicked button - update.callback_query.message
    If none of the above, return None
    """
    if update.message:
        return update.message.reply_text
    elif update.callback_query and update.callback_query.message:
        return update.callback_query.message.reply_text
    else:
        return None