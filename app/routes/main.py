from flask import Blueprint, jsonify, render_template


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return render_template('index.html')


@main_bp.route('/faq')
def faq():
    return render_template('faq.html')


@main_bp.route('/health', methods=['GET'])
def health():
    return jsonify(status='ok'), 200
