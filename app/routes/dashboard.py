from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Consultation
from ..utils.auth import get_current_user, login_required_json, login_required_page
from ..utils.db import safe_commit, safe_commit_json


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required_page
def dashboard():
    user = get_current_user()
    if not user:
        session.pop('user_id', None)
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        symptoms = request.form['symptoms']
        consultation = Consultation(user_id=user.id, symptoms=symptoms)
        db.session.add(consultation)
        if safe_commit('Consultation form submitted successfully!'):
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('dashboard.dashboard'))

    # Paginate active consultations
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 5))
    
    pagination = (Consultation.query
                 .filter_by(user_id=user.id, is_deleted=False)
                 .order_by(Consultation.created_at.desc())
                 .paginate(page=page, per_page=per_page, error_out=False))
                 
    consultations = pagination.items
    return render_template(
        'dash.html', 
        user=user, 
        consultations=consultations, 
        pagination=pagination
    )


@dashboard_bp.route('/update_consultation/<int:id>', methods=['GET', 'POST'])
@login_required_page
def update_consultation(id):
    consultation = Consultation.query.filter_by(id=id, is_deleted=False).first_or_404()
    if consultation.user_id != session['user_id']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        consultation.symptoms = request.form['symptoms']
        consultation.updated_at = datetime.utcnow()
        if safe_commit('Consultation updated successfully!'):
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('dashboard.dashboard'))

    return render_template('update_consultation.html', consultation=consultation)


@dashboard_bp.route('/delete_consultation/<int:id>', methods=['POST'])
@login_required_json
def delete_consultation(id):
    consultation = Consultation.query.filter_by(id=id, is_deleted=False).first_or_404()
    if consultation.user_id != session['user_id']:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    # Perform soft delete instead of database delete
    consultation.is_deleted = True
    ok, err = safe_commit_json()
    if ok:
        return jsonify({"success": True, "message": "Consultation deleted successfully"})
    return jsonify({"success": False, "message": f"Delete failed: {err}"}), 500


@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required_page
def profile():
    user = get_current_user()
    if not user:
        session.clear()
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user.name = request.form.get('name', user.name)
        user.phone = request.form.get('phone', user.phone)
        user.age = request.form.get('age', type=int)
        user.gender = request.form.get('gender')
        user.blood_group = request.form.get('blood_group')
        user.medical_history = request.form.get('medical_history')
        user.allergies = request.form.get('allergies')

        if safe_commit('Profile updated successfully!'):
            return redirect(url_for('dashboard.profile'))
        return redirect(url_for('dashboard.profile'))

    return render_template('profile.html', user=user)


@dashboard_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required_json
def update_status(id):
    consultation = Consultation.query.filter_by(id=id, is_deleted=False).first_or_404()

    data = request.json
    new_status = data.get('status')
    doctor_notes = data.get('doctor_notes')

    if new_status:
        consultation.status = new_status
    if doctor_notes:
        consultation.doctor_notes = doctor_notes

    consultation.updated_at = datetime.utcnow()
    ok, err = safe_commit_json()
    if ok:
        return jsonify({"success": True, "message": "Status updated successfully"})
    return jsonify({"success": False, "message": f"Update failed: {err}"}), 500
