import MySQLdb
from flask import g
from app.config import Config

def get_db():
    if 'db' not in g:
        g.db = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB,

        )
    return g.db

def close_db():
    """Close database connection"""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database and create tables if they don't exist"""
    db = get_db()
    cursor = db.cursor()

    # Admins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            emp_id VARCHAR(20) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)

    # Employees Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            emp_id VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            otp VARCHAR(6),
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
    """)

    # Form Responses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS form_responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            emp_id VARCHAR(20) NOT NULL,
            response TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    db.commit()
    print("✅ Database Initialized!")
