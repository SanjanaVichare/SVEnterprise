import datetime
from email.mime.multipart import MIMEMultipart
import random
import smtplib
import pandas as pd
from email.mime.text import MIMEText

import pymysql
import qrcode
from app.config import Config
from flask import current_app, jsonify
import os
import ssl
from datetime import datetime
from flask import (
    jsonify
)
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import mysql.connector
from app.config import Config
import os
from flask import jsonify
from datetime import datetime
import os
import csv
import json
from flask import (
    jsonify
)
import mysql
from app.config import Config
from app.database import get_db
from app.utils import *

def get_mysql_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        passwd=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        autocommit=True
    )

def is_response_already_saved(emp_id, submission_date):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM google_form_response WHERE emp_id = %s AND submission_date = %s"
        cursor.execute(query, (emp_id, submission_date))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception as e:
        print("❌ Error checking duplicates:", e)
        return False




def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None  # Handle invalid dates gracefully

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    """Send OTP via HTML-styled Email"""
    try:
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            print("❌ Error: Missing SMTP credentials in Config.")
            return False

        subject = "🔐 Your OTP Code for Verification"

        # HTML Email Body
        html_body = f"""
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
                body {{
                    font-family: 'Poppins', sans-serif;
                    background-color: #f4f8fb;
                    color: #333333;
                    padding: 20px;
                }}
                .container {{
                    max-width: 500px;
                    margin: auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    padding: 30px;
                }}
                .otp-box {{
                    background-color: #e0f0ff;
                    border: 2px dashed #0077cc;
                    padding: 16px;
                    text-align: center;
                    font-size: 28px;
                    font-weight: 600;
                    color: #0077cc;
                    letter-spacing: 2px;
                    border-radius: 8px;
                    margin-top: 20px;
                    margin-bottom: 30px;
                }}
                .footer {{
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color:#2c3e50;">Hello 👋</h2>
                <p>Here is your one-time password (OTP) for secure verification:</p>
                <div class="otp-box">{otp}</div>
                <p>This OTP is valid for a limited time. Please do not share it with anyone.</p>
                <div class="footer">
                    <p>If you don't receive an OTP please try again.</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        # Prepare MIME message
        msg = MIMEMultipart("alternative")
        msg["From"] = Config.MAIL_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        # Send via SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
            server.starttls(context=context)
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, to_email, msg.as_string())

        print(f"✅ OTP Sent Successfully to {to_email}!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Authentication Error: Incorrect username/password.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    return False


def export_to_excel(data, filename="exported_data.xlsx"):
    """Export data to an Excel file."""
    if not data:
        return jsonify({"error": "No data to export"}), 400

    df = pd.DataFrame(data)

    file_path = os.path.join("exports", filename)
    os.makedirs("exports", exist_ok=True)  # Ensure the exports directory exists
    df.to_excel(file_path, index=False)

    return file_path

def get_db_connection():
    return mysql.connector.connect(
        host="shalakapoojari.mysql.pythonanywhere-services.com",
        user="shalakapoojari",
        password="Shalaka@250125",
        database="shalakapoojari$sv"
    )

# Ensure output folder exists
output_folder = "generated_cards/"
os.makedirs(output_folder, exist_ok=True)

def generate_employee_code(emp_number):
    """Generate Employee ID"""
    return f"{str(emp_number).zfill(3)}"

def get_employee_by_id(emp_id):
    """Fetch Employee Data from MySQL"""
    try:
        connection = get_db()
        cursor = connection.cursor()

        emp_id = emp_id.strip().strip('"').strip("'")  # Clean input
        query = "SELECT * FROM employees WHERE emp_id = %s"

        print(f"Executing: {query} with {emp_id}")  # Debugging output
        cursor.execute(query, (emp_id,))
        employee = cursor.fetchone()

        print("Fetched Employee Data:", employee)
        return employee

    except pymysql.MySQLError as e:
        print(f"MySQL Error: {e}")
        return None

    finally:
        cursor.close()  # Close cursor, but keep connection open


from PIL import Image, ImageDraw, ImageFont

def load_fonts():
    font_dir = os.path.join(current_app.root_path, "fonts")
    try:
        title_font = ImageFont.truetype(os.path.join(font_dir, "Poppins-Bold.ttf"), 35)
        bold_font  = ImageFont.truetype(os.path.join(font_dir, "Poppins-Bold.ttf"), 30)
        text_font  = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 25)
    except IOError:
        print("⚠️ Font files not found. Using default system font.")
        title_font = bold_font = text_font = ImageFont.load_default()
    return title_font, bold_font, text_font


def draw_justified_text(draw, text, position, font, max_width, bold_name=None):
    words = text.split()
    lines, line, line_width = [], [], 0
    space_w = draw.textbbox((0, 0), " ", font=font)[2]

    for word in words:
        w = draw.textbbox((0, 0), word, font=font)[2]
        if line and line_width + w + space_w > max_width:
            lines.append((line, line_width))
            line, line_width = [], 0
        line.append(word)
        line_width += w + (space_w if line else 0)
    if line:
        lines.append((line, line_width))

    y = position[1]
    for ln, ln_w in lines:
        if len(ln) == 1:
            draw.text((position[0], y), ln[0], fill="black", font=font)
        else:
            total_spacing = max_width - ln_w
            extra = total_spacing // (len(ln) - 1)
            x = position[0]
            for word in ln[:-1]:
                f = font_bold if bold_name and word == bold_name else font
                draw.text((x, y), word, fill="black", font=f)
                x += draw.textbbox((0, 0), word, font=f)[2] + space_w + extra
            draw.text((x, y), ln[-1], fill="black",
                      font=font_bold if bold_name and ln[-1] == bold_name else font)
        y += font.getbbox("A")[3] - font.getbbox("A")[1] + 10


def create_id_card(employee_data):
    from PIL import Image, ImageDraw
    import qrcode

    # --- Canvas setup ------------------------------------------------------
    W, H = 600, 980
    card = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(card)

    # --- Load custom fonts -------------------------------------------------
    global font_bold
    font_title, font_bold, font_text = load_fonts()

    # --- Company logo ------------------------------------------------------
    logo_path = os.path.join(current_app.root_path, "static", "assets", "logo.jpg")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).resize((400, 80))
        card.paste(logo, ((W - 400) // 2, 20))

    # --- Heading -----------------------------------------------------------
    draw.text((13, 120), "AUTHORIZED COLLECTION AGENT", fill="black", font=font_title)

    # --- Employee photo ----------------------------------------------------
    card.paste(employee_data["Photo"].resize((180, 180)), (210, 180))

    # --- Key/value fields --------------------------------------------------
    y = 380
    fields = [
        ("Name",         employee_data["Name"]),
        ("Designation",  employee_data["Designation"]),
        ("Phone No.",    employee_data["Phone No."]),
        ("ID Card No",   employee_data["ID Card No"]),
    ]
    for lbl, val in fields:
        draw.text((50,  y), f"{lbl}:",  fill="black", font=font_text)
        draw.text((250, y), str(val),   fill="black", font=font_bold)
        y += 40

    # --- Certificate paragraph ---------------------------------------------
    para = (
        "TO WHOMSOEVER IT MAY CONCERN\n\n"
        "This is to certify that "
        f"{employee_data['Name']} is an employee of\n"
        "S V ENTERPRISES. They are authorized to collect\n"
        "money (Cash, Cheques, or Demand Drafts) from customers,\n"
        "provided that a valid receipt is issued in return."
    )
    draw_justified_text(draw, para, (50, y + 20), font_text, 500,
                        bold_name=employee_data["Name"])

    # --- QR code -----------------------------------------------------------
    qr_data = (
        f"ID: {employee_data['ID Card No']}\n"
        f"Name: {employee_data['Name']}\n"
        f"Designation: {employee_data['Designation']}\n"
        f"Phone: {employee_data['Phone No.']}\n"
        f"Blood Group: {employee_data['Blood Group']}\n"
        f"Date of Joining: {employee_data['Date of Joining']}"
    )
    qr = qrcode.QRCode(box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    card.paste(qr.make_image(fill="black", back_color="white").resize((150, 150)),
               (220, 820))

    return card
