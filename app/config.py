import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

    # MySQL for PythonAnywhere
    MYSQL_HOST = 'SVEnterprise.mysql.pythonanywhere-services.com'
    MYSQL_USER = 'SVEnterprise'
    MYSQL_PASSWORD = 'SVE@DB21'
    MYSQL_DB = 'SVEnterprise$sv'
    print("Loaded MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
    print("Loaded SECRET_KEY:", os.getenv("SECRET_KEY"))

    # Email
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "sventerprise01@gmail.com"
    MAIL_PASSWORD = "webl yztc yvjo sipj"

    # Uploads
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'uploads')
