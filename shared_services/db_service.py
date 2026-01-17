# services/data_service.py
# TAGS: [status_validation], [get_data], [create_data], [update_data], [directory_path], [file_path], [persistent_keyboard], [format_data]
# Shared data service for manager_bot, consultant_bot, and applicant_bot

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Type, Any, Dict

# Add project root to path to access shared config.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from telegram import Update
from sqlalchemy import select, Boolean, String

from config import *
from database import SessionLocal, Managers, Vacancies, Applicants, Base
from shared_services.constants import (
    BOT_FOR_APPLICANTS_USERNAME,
    AUTH_REQ_TEXT,
    AUTH_SUCCESS_TEXT,
    AUTH_FAILED_TEXT,
    PRIVACY_POLICY_CONFIRMATION_TEXT,
    SUCCESS_TO_GET_PRIVACY_POLICY_CONFIRMATION_TEXT,
    MISSING_PRIVACY_POLICY_CONFIRMATION_TEXT_MANAGER as MISSING_PRIVACY_POLICY_CONFIRMATION_TEXT,
    MISSING_VACANCY_SELECTION_TEXT,
    RESUME_PASSED_SCORE,
    INVITE_TO_INTERVIEW_CALLBACK_PREFIX,
    FEEDBACK_REQUEST_TEXT,
    FEEDBACK_SENT_TEXT,
    WELCOME_VIDEO_RECORD_REQUEST_TEXT,
    VIDEO_SENDING_CONFIRMATION_TEXT,
    MISSING_VIDEO_RECORD_TEXT,
)
from config import HH_CLIENT_ID, OAUTH_REDIRECT_URL

logger = logging.getLogger(__name__)


# ****** [create_data] ******

def create_record_for_new_user_in_db(db_model: Type[Base], record_id: str) -> None:
    """ Args:
        record_id: The ID to create (as string)
        db_model: The database model class (Managers, Vacancies, Applicants, etc.)
    """
    id_column = db_model.__table__.columns.get("id")
    if id_column is None:
        logger.error(f"{db_model.__name__} does not have id column")
        return

    if not isinstance(id_column.type, String):
        logger.error(f"{db_model.__name__}.id is not a String column")
        return

    record_id_value: Any = record_id

    db = SessionLocal()
    try:
        if db.query(db_model).filter(id_column == record_id_value).first():
            logger.debug(f"{db_model.__name__} {record_id} уже существует.")
            return
        # create new user record in database with minimum available attributes, other attributes will be updated later
        new_record = db_model(
            id=record_id_value,
            first_time_seen=datetime.now(timezone.utc)
        )
        db.add(new_record)
        db.commit()
        logger.debug(f"{db_model.__name__} {record_id} добавлен в БД")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании пользователя {record_id}: {e}")
        raise
    finally:
        db.close()


# ****** [status_validation] ******


def is_boolean_field_true_in_db(db_model: Type[Base], record_id: str, field_name: str) -> bool:
    
    method_name_for_logging = f"is_boolean_field_true_in_db: {db_model.__name__}.{field_name}"

    # ---- Validate the model/column before querying ----

    # fetches the column object by name
    column = db_model.__table__.columns.get(field_name)
    if column is None:
        logger.warning(f"{method_name_for_logging} does not have column {field_name}")
        return False
    # ensures the column is a Boolean
    if not isinstance(column.type, Boolean):
        logger.warning(f"{method_name_for_logging} is not a Boolean column")
        return False
    # ensures the model has an id column
    id_column = db_model.__table__.columns.get("id")
    if id_column is None:
        logger.warning(f"{method_name_for_logging} does not have id column")
        return False

    if not isinstance(id_column.type, String):
        logger.error(f"{method_name_for_logging}.id is not a String column")
        return False

    with SessionLocal() as db:
        value = db.execute(
            select(column).where(id_column == record_id)
        ).scalar_one_or_none()

    if value is None:
        logger.debug(f"{method_name_for_logging} {record_id} not found in database")
        return False

    return value


def is_value_in_db(db_model: Type[Base], field_name: str, value: Any) -> bool:
    
    method_name_for_logging = f"is_value_in_db: {db_model.__name__}.{field_name}"

    column = db_model.__table__.columns.get(field_name)
    if column is None:
        logger.warning(f"{method_name_for_logging} does not have column {field_name}")
        return False

    with SessionLocal() as db:
        match = db.execute(
            select(column).where(column == value)
        ).scalar_one_or_none()

    # returns True if the value is found in the database, False otherwise
    return match is not None


# ****** [get_data] ******

def get_column_value_in_db(db_model: Type[Base], record_id: str, field_name: str) -> Any:

    method_name_for_logging = f"get_column_value_in_db: {db_model.__name__}.{field_name}"

    column = db_model.__table__.columns.get(field_name)
    if column is None:
        logger.warning(f"{method_name_for_logging} does not have column {field_name}")
        return None

    id_column = db_model.__table__.columns.get("id")
    if id_column is None:
        logger.warning(f"{method_name_for_logging} does not have id column")
        return None

    if not isinstance(id_column.type, String):
        logger.error(f"{method_name_for_logging}.id is not a String column")
        return None

    with SessionLocal() as db:
        value = db.execute(
            select(column).where(id_column == record_id)
        ).scalar_one_or_none()

    return value

# ****** [update_data] ******

def update_record_in_db(db_model: Type[Base], record_id: str, updates: Dict[str, Any]) -> None:

    method_name_for_logging = f"update_record_in_db: {db_model.__name__}.{record_id}"

    if not updates:
        logger.warning(f"{method_name_for_logging} no updates provided")
        return

    id_column = db_model.__table__.columns.get("id")
    if id_column is None:
        logger.error(f"{method_name_for_logging} does not have id column")
        return
    if not isinstance(id_column.type, String):
        logger.error(f"{method_name_for_logging}.id is not a String column")
        return

    db = SessionLocal()
    try:
        result = db.query(db_model).filter(id_column == record_id).update(updates)
        if result == 0:
            logger.debug(f"{method_name_for_logging} not found in database")
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"{method_name_for_logging} error: {e}")
        raise
    finally:
        db.close()


def clear_column_value_in_db(db_model: Type[Base], record_id: str, field_name: str) -> None:
    
    method_name_for_logging = f"clear_column_value_in_db: {db_model.__name__}.{record_id}.{field_name}"

    column = db_model.__table__.columns.get(field_name)
    if column is None:
        logger.warning(f"{method_name_for_logging} does not have column {field_name}")
        return

    id_column = db_model.__table__.columns.get("id")
    if id_column is None:
        logger.error(f"{method_name_for_logging} does not have id column")
        return
    if not isinstance(id_column.type, String):
        logger.error(f"{method_name_for_logging}.id is not a String column")
        return

    db = SessionLocal()
    try:
        result = db.query(db_model).filter(id_column == record_id).update({field_name: None})
        if result == 0:
            logger.debug(f"{method_name_for_logging} not found in database")
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"{method_name_for_logging} error: {e}")
        raise
    finally:
        db.close()

