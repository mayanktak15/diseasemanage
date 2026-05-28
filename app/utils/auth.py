from functools import wraps

from flask import flash, jsonify, redirect, session, url_for

from ..extensions import db
from ..models import User


def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return db.session.get(User, uid)


def login_required_page(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    return wrapper


def login_required_json(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Please log in"}), 401
        return view_func(*args, **kwargs)
    return wrapper
