from flask import Flask
from app.database import get_db, close_db, init_db
from dotenv import load_dotenv
load_dotenv()


def create_app():

    app = Flask(__name__)

    # Load configurations
    app.config.from_object("app.config.Config")

    # Initialize database
    with app.app_context():
        init_db()  # Ensure DB tables exist

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Ensure database connection is closed after each request
    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db()

    return app
