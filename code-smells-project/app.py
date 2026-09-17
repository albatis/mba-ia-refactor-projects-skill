import logging

from flask import Flask
from flask_cors import CORS

from src.config import database
from src.config.settings import DEBUG, SECRET_KEY
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import bp as api_bp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    CORS(app)
    database.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(api_bp)

    return app


app = create_app()

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
