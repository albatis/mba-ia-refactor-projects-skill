import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "dev-admin-key-change-me")
