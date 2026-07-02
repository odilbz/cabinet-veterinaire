import os
import sys


# -----------------------------------------------------------
# PATH HELPERS (for packaging into a standalone .exe)
# -----------------------------------------------------------
def is_frozen():
    return getattr(sys, "frozen", False)


def resource_path(relative_path):
    if is_frozen():
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)


def get_app_data_dir():
    if is_frozen():
        app_dir = os.path.join(os.path.expanduser("~"), "CabinetVeterinaire")
    else:
        app_dir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "vet-clinic-super-secret-key-2026"
    DB_DIR = get_app_data_dir()
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(DB_DIR, "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ["fr", "ar", "en"]
    HOST = "127.0.0.1"
    PORT = 5000
