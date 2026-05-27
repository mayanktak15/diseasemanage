from flask import jsonify, render_template, request


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        if request.accept_mimetypes.accept_html and not request.is_json:
            return render_template('error_403.html'), 403
        return jsonify(error='Forbidden'), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.accept_mimetypes.accept_html and not request.is_json:
            return render_template('error_404.html'), 404
        return jsonify(error='Not Found'), 404

    @app.errorhandler(500)
    def server_error(error):
        if request.accept_mimetypes.accept_html and not request.is_json:
            return render_template('error_500.html'), 500
        return jsonify(error='Internal Server Error'), 500
