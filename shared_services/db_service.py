# services/data_service.py
# TAGS: [status_validation], [get_data], [create_data], [update_data], [directory_path], [file_path], [persistent_keyboard], [format_data]
# Shared data service for manager_bot, consultant_bot, and applicant_bot

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Type, Any

# Add project root to path to access shared config.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from telegram import Update

from config import *
from database import SessionLocal, Manager, Vacancy, Resume, Base
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

def create_record_for_new_user_in_db(record_id: str, db_model: Type[Base]) -> None:
    """ Args:
        record_id: The ID to create (as string)
        db_model: The database model class (Manager, Resume, Vacancy, etc.)
    """
    db = SessionLocal()
    try:
        if db.query(db_model).filter(db_model.id == int(record_id)).first():
            logger.debug(f"{db_model.__name__} {record_id} уже существует.")
            return
        # create new user record in database with minimum available attributes, other attributes will be updated later
        new_record = db_model(
            id=int(record_id),
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


def is_user_in_db(record_id: str, db_model: Type[Base]) -> bool:
    """ Args:
        record_id: The ID to check (as string)
        db_model: The database model class (Manager, Resume, Vacancy, etc.)
    """
    db = SessionLocal()
    try:
        if db_model == Manager:
            return db.query(db_model).filter(db_model.id == int(record_id)).first() is not None
        elif db_model == Resume:
            return db.query(db_model).filter(db_model.id == record_id).first() is not None
        else:
            logger.error(f"Неизвестная модель: {db_model.__name__}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке наличия записи {record_id} в БД (модель: {db_model.__name__}): {e}")
        return False
    finally:
        db.close()


# ****** [update_data] ******

def update_user_record_id_db(record_id: str, db_model: Type[Base], key: str, value: Any) -> None:
    """ Args:
        record_id: The ID to update (as string)
        db_model: The database model class (Manager, Resume, Vacancy, etc.)
        key: The key/attribute name to update
        value: The value to set for the key
    """
    db = SessionLocal()
    try:
        db.query(db_model).filter(db_model.id == int(record_id)).update({key: value})
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении записи {record_id} в БД (модель: {db_model.__name__}): {e}")
        raise
    finally:
        db.close()