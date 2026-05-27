from app import create_app
from app.extensions import db
from app.models import Consultation, User


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000)
