from flask import current_app, flash

from ..extensions import db


def safe_commit(success_message: str | None = None, error_message: str | None = None) -> bool:
    try:
        db.session.commit()
        if success_message:
            flash(success_message, 'success')
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"DB commit failed: {e}")
        if error_message:
            flash(error_message, 'error')
        return False


def safe_commit_json() -> tuple[bool, str | None]:
    try:
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"DB commit failed: {e}")
        return False, str(e)
