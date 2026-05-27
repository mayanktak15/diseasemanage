from flask import Blueprint, jsonify, request, session, current_app

from ..extensions import limiter
from ..models import Consultation
from ..services.chatbot_service import get_chatbot_response


chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/chatbot', methods=['POST'])
@limiter.limit('10 per minute')
def chatbot():
    data = request.get_json(silent=True) or {}
    query = data.get('message')
    current_app.logger.info('chatbot query received')

    if not query:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        with open('query_dataset.csv', 'a', encoding='utf-8', newline='') as file:
            safe_query = (query or '').replace('\r', ' ').replace('\n', ' ').strip()
            file.write(safe_query + "\n")
    except Exception as exc:
        current_app.logger.warning(f"Could not append to query_dataset.csv: {exc}")

    if 'user_id' in session:
        latest_consultation = Consultation.query.filter_by(user_id=session['user_id']).order_by(
            Consultation.created_at.desc()).first()
        symptoms = latest_consultation.symptoms if latest_consultation else None
    else:
        symptoms = None

    try:
        response = get_chatbot_response(query, symptoms)
        if response and str(response).strip():
            return jsonify({"reply": response})

        return jsonify({"reply": "I'm sorry, I couldn't generate a response. Please try asking about Docify Online services."})
    except Exception as exc:
        current_app.logger.exception(f"Error in chatbot endpoint: {exc}")

        fallback_response = (
            "Welcome to Docify Online! I'm here to help you with:\n"
            "- Information about our medical consultation services\n"
            "- How to submit consultation forms\n"
            "- FAQ about our platform\n"
            "- General health information guidance\n\n"
            "What would you like to know about Docify Online?"
        )
        return jsonify({"reply": fallback_response})
