from datetime import timedelta
import re
import secrets
import MySQLdb
from flask import (
    Blueprint, app, current_app, render_template, request, redirect, url_for, session, flash, send_file, jsonify
)
from app.database import get_db
from app.utils import generate_otp, send_otp_email, export_to_excel
import os
import csv
from io import StringIO
from flask import Response, request, jsonify
import os
import csv
import io
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    send_file, jsonify, Response
)
import mysql
from app.database import get_db
from app.utils import *
from functools import wraps
from flask import session, redirect, url_for, flash
from functools import wraps
from flask import make_response
from flask import request, jsonify
from datetime import datetime, timedelta
from app.database import get_db
import calendar
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors

main_bp = Blueprint("main", __name__)


main_bp.permanent_session_lifetime = timedelta(minutes=30)

@main_bp.before_request
def make_session_permanent():
    session.permanent = True

#removing cachr to not let it login again
def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in as admin to access this page', 'danger')
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'emp_id' not in session:
            flash('Please log in as employee to access this page', 'danger')
            return redirect(url_for('main.employee_login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/employee/login", methods=["GET", "POST"])
def employee_login():
    if request.method == "POST":
        emp_id = request.form["emp_id"]  # ❌ You were overwriting this
        email = request.form["email"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT emp_id, email, status FROM employees WHERE emp_id = %s AND email = %s", (emp_id, email))
        user = cursor.fetchone()

        if user:
            emp_status = user[2]

            if emp_status == "Blocked":
                flash("❌ Your account is blocked. Contact Admin.", "danger")
                return redirect(url_for("main.employee_login"))

            # ✅ Set session AFTER successful validation
            session["emp_id"] = emp_id
            session["email"] = email

            # Generate OTP
            otp = generate_otp()
            cursor.execute("UPDATE employees SET otp = %s WHERE emp_id = %s", (otp, emp_id))
            db.commit()

            send_otp_email(email, otp)
            flash("✅ OTP sent to your email!", "success")
            return redirect(url_for("main.otp_verification"))
        else:
            flash("❌ Invalid Employee ID or Email!", "danger")

    return render_template("employeelogin.html")



@main_bp.route("/otp-verification", methods=["GET", "POST"])
def otp_verification():
    if "emp_id" not in session:
        return redirect(url_for("main.employee_login"))

    if request.method == "POST":
        entered_otp = request.form["otp"]
        emp_id = session["emp_id"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT email, otp FROM employees WHERE emp_id = %s", (emp_id,))
        result = cursor.fetchone()

        if result and entered_otp == result[1]:
            cursor.execute("UPDATE employees SET otp = NULL WHERE emp_id = %s", (emp_id,))
            cursor.execute("INSERT INTO login_activity (emp_id, email) VALUES (%s, %s)", (emp_id, result[0]))
            db.commit()
            return redirect(url_for("main.employee_dashboard"))
        else:
            flash("❌ Invalid OTP. Please try again.", "danger")

    return render_template("otp_verification.html")


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        emp_id = request.form["emp_id"].strip()
        password = request.form["password"].strip()

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM admins WHERE emp_id = %s", (emp_id,))
        admin = cursor.fetchone()

        if admin:
            # Convert to dictionary
            columns = [col[0] for col in cursor.description]
            admin_dict = dict(zip(columns, admin))

            # Try common password field names
            password_field = next(
                (f for f in ['password', 'pwd', 'pass', 'password_hash']
                 if f in admin_dict),
                None
            )

            if password_field and admin_dict[password_field] == password:
                session["admin_id"] = emp_id
                return redirect(url_for("main.admin_dashboard"))

        flash("Invalid credentials", "error")

    return render_template("adminlogin.html")

@main_bp.route("/admin/dashboard")
@nocache
def admin_dashboard():
    try:
        if "admin_id" not in session:
            return redirect(url_for("main.admin_login"))

        db = get_db()
        cursor = db.cursor()

        # Fetch login records
        cursor.execute("SELECT emp_id, email, login_time FROM login_activity ORDER BY login_time DESC")
        login_records = cursor.fetchall()

        # Fetch form visibility
        cursor.execute("SELECT is_visible FROM form_visibility WHERE id = 1")
        result = cursor.fetchone()
        form_visibility = result[0] if result else 0

        return render_template("admindashboard.html", login_records=login_records, form_visible=form_visibility)

    except Exception as e:
        print("Form visibility fetch failed:", e)
        return render_template("admindashboard.html", login_records=[], form_visible=0)


@main_bp.route("/export-data")
@nocache
def export_data():
    if "admin_id" not in session:
        return redirect(url_for("main.admin_login"))

    file_path = export_to_excel()
    return send_file(file_path, as_attachment=True) if os.path.exists(file_path) else redirect(url_for("main.admin_dashboard"))

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))



@main_bp.route("/employee_logout")
def employee_logout():
    emp_id = session.get("emp_id")
    email = session.get("email")

    if not emp_id or not email:
        print("Session missing 'emp_id' or 'email'")
        return redirect(url_for("main.index"))

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE login_activity
                SET logout_time = %s
                WHERE emp_id = %s AND email = %s AND logout_time IS NULL
                ORDER BY login_time DESC
                LIMIT 1
            """, (datetime.now(), emp_id, email))
        db.commit()
    except Exception as e:
        print("❌ Logout update failed:", e)

    session.clear()
    return redirect(url_for("main.index"))

@main_bp.route("/admin/toggle-visibility", methods=["POST"])
def toggle_visibility():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_visible FROM form_visibility WHERE id = 1")
        current_visibility = cursor.fetchone()[0]
        new_visibility = 0 if current_visibility == 1 else 1
        cursor.execute("UPDATE form_visibility SET is_visible = %s WHERE id = 1", (new_visibility,))
        db.commit()

        # ✅ Add message in JSON response
        message = "Form has been enabled" if new_visibility == 1 else "Form has been disabled"
        return jsonify({"success": True, "new_visibility": new_visibility, "message": message})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)})



@main_bp.route("/check_response_count")
@nocache
def check_response_count():
    manager = request.args.get("manager", "").strip()
    emp_id = request.args.get("emp_id", "").strip()
    month = request.args.get("month", "").strip()

    query = "SELECT COUNT(*) FROM google_form_response WHERE 1=1"
    params = []

    if manager:
        query += " AND LOWER(manager_name) LIKE %s"
        params.append(f"%{manager.lower()}%")
    if emp_id:
        query += " AND LOWER(emp_id) LIKE %s"
        params.append(f"{emp_id.lower()}%")
    if month:
        query += " AND CAST(month AS TEXT) = %s"
        params.append(month)
    db=get_db()

    cur = db.cursor()
    cur.execute(query, tuple(params))
    count = cur.fetchone()[0]
    cur.close()

    return jsonify({"count": count})

@main_bp.route('/submit', methods=['POST'])
def submit_form():
    if not request.form:
        flash("No form data received", "danger")
        return redirect(url_for("main.employee_dashboard"))

    try:
        form_data = request.form
        emp_id = session.get('emp_id')
        month_of_submission = form_data.get('month_of_submission')

        if not emp_id or not month_of_submission:
            flash("Required fields are missing", "danger")
            return redirect(url_for("main.employee_dashboard"))

        # Sanitize and validate fields
        name = form_data.get('name', '').strip()
        phoneno = form_data.get('phoneno', '').strip()
        company_contact = form_data.get('company_contact', '').strip()
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        phone_pattern = r'^\d{10}$'

        errors = []

        if not name:
            errors.append("Name is required.")
        if not re.match(phone_pattern, phoneno):
            errors.append("Phone number must be a valid 10-digit number.")
        if not re.match(phone_pattern, company_contact):
            errors.append("Company contact must be a valid 10-digit number.")
        if not form_data.get('portfolio_name', '').strip():
            errors.append("Portfolio name is required.")
        if not form_data.get('designation', '').strip():
            errors.append("Designation is required.")
        if not form_data.get('doi', '').strip():
            errors.append("Date of joining is required.")
        if not form_data.get('manager_name', '').strip():
            errors.append("Manager name is required.")
        if not form_data.get('supervisor_name', '').strip():
            errors.append("Supervisor name is required.")
        if not form_data.get('telecaller_name', '').strip():
            errors.append("Telecaller name is required.")

        try:
            allocation_count = int(form_data.get('allocation_count', 0))
            total_calls = int(form_data.get('total_calls', 0))
            monthly_collection = int(form_data.get('monthly_collection',0))
        except ValueError:
            errors.append("Allocation count, total calls, and monthly collection must be integers.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect(url_for("main.employee_dashboard"))

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT is_visible FROM form_visibility WHERE id = 1")
            if not cursor.fetchone()[0]:
                flash("Form submissions are currently disabled by admin", "danger")
                return redirect(url_for("main.employee_dashboard"))

            cursor.execute(
                """SELECT submitted_at FROM google_form_response
                WHERE emp_id = %s AND month_of_submission = %s""",
                (emp_id, month_of_submission)
            )
            if cursor.fetchone():
                flash("You have already submitted the form for this month!", "warning")
                return redirect(url_for("main.employee_dashboard"))

            insert_sql = '''
                INSERT INTO google_form_response (
                    name, emp_id, phoneno, company_contact,
                    portfolio_name, designation, doi, manager_name,
                    supervisor_name, telecaller_name, allocation_count, total_calls,
                    monthly_collection, bank_id, month_of_submission, submitted_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            '''

            insert_data = (
                name,
                emp_id,
                phoneno,
                company_contact,
                form_data.get('portfolio_name'),
                form_data.get('designation'),
                form_data.get('doi'),
                form_data.get('manager_name'),
                form_data.get('supervisor_name'),
                form_data.get('telecaller_name'),
                allocation_count,
                total_calls,
                monthly_collection,
                null_if_empty(form_data.get('bank_id')),
                month_of_submission
            )

            cursor.execute(insert_sql, insert_data)
            db.commit()
            flash("Your response has been successfully stored!", "success")

        return redirect(url_for("main.employee_dashboard"))

    except Exception as e:
        current_app.logger.error(f"Form submission error: {str(e)}")
        flash("An error occurred during form submission", "danger")
        return redirect(url_for("main.employee_dashboard"))


def null_if_empty(value):
    return value.strip() if value and value.strip() else None



@main_bp.route("/admin/download-activity")
@nocache
def download_activity():
    if "admin_id" not in session:
        return redirect(url_for("main.admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
    "SELECT emp_id, email, login_time, logout_time FROM login_activity"
    )
    logs = cursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee ID", "Email", "Login Time","Logout Time"])
    writer.writerows(logs)
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=login_activity.csv"})

@main_bp.route("/api/login-activity")
def api_login_activity():

    db = get_db()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT emp_id, email, login_time, logout_time FROM login_activity ORDER BY login_time DESC")
    rows = cursor.fetchall()
    return jsonify({"success": True, "data": rows})

@main_bp.route("/employee/dashboard")
@nocache
@employee_required
def employee_dashboard():
    try:
        if "emp_id" not in session:
            flash("Session expired. Please login again.", "danger")
            return redirect(url_for("main.employee_login"))

        emp_id = session["emp_id"]
        db = get_db()

        with db.cursor() as cursor:
            # Get form visibility status
            cursor.execute("SELECT is_visible FROM form_visibility WHERE id = 1")
            form_visible_result = cursor.fetchone()
            form_visible = bool(form_visible_result[0]) if form_visible_result else False

            # Get current month name (e.g. "January")
            current_month = datetime.now().strftime("%B")

            # Check for existing submission this month
            cursor.execute(
                """SELECT submitted_at FROM google_form_response
                WHERE emp_id = %s AND month_of_submission = %s""",
                (emp_id, current_month)
            )
            already_submitted = cursor.fetchone() is not None

            # Get employee details
            cursor.execute(
                """SELECT emp_id, name, phoneno, designation, doi
                FROM employees WHERE emp_id = %s""",
                (emp_id,)
            )
            employee_data = cursor.fetchone()

            if not employee_data:
                flash("Employee data not found", "danger")
                return redirect(url_for("main.employee_login"))

            employee = {
                "emp_id": employee_data[0],
                "name": employee_data[1],
                "phoneno": employee_data[2],
                "designation": employee_data[3],
                "doi": employee_data[4]
            }

        return render_template(
            "employeedashboard.html",
            form_visible=form_visible,
            already_submitted=already_submitted,
            employee=employee,
            month_of_submission=current_month
        )

    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        flash("Error loading dashboard. Please try again.", "danger")
        return redirect(url_for("main.employee_login"))

@main_bp.route("/download_responses", methods=["GET"])
@nocache
def download_responses():
    manager_name = request.args.get("manager_name")
    emp_id = request.args.get("emp_id")
    month = request.args.get("month")

    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    # Always define responses to prevent UnboundLocalError
    responses = []

    query = "SELECT * FROM google_form_response"
    conditions = []
    params = []

    if manager_name:
        conditions.append("manager_name = %s")
        params.append(manager_name)
    if emp_id:
        conditions.append("emp_id = %s")
        params.append(emp_id)
    if month:
        try:
            month_int = int(month)
            conditions.append("MONTH(submitted_at) = %s")
            params.append(month_int)
        except ValueError:
            pass  # silently ignore bad month input

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    print("SQL:", query)
    print("Params:", params)

    cursor.execute(query, params)
    responses = cursor.fetchall()

    if not responses:
        return jsonify({"error": "No responses found"}), 404

    # Generate CSV
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow([
        "ID", "Employee ID", "Full Name", "Mobile Number", "Company Contact",
        "Portfolio Name", "Designation", "Joining Date", "Manager Name",
        "Supervisor Name", "Telecaller Name", "Allocation Count",
        "Total Calls/Visits", "Total Monthly Collection", "Bank ID",
        "PVC Number", "Submission Date"
    ])
    for row in responses:
        csv_writer.writerow(row)

    csv_output.seek(0)
    return Response(
        csv_output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=google_form_responses.csv"}
    )



@main_bp.route("/view_filtered_responses", methods=["GET"])
@nocache
def view_filtered_responses():
    manager_name = request.args.get("manager_name")
    emp_id = request.args.get("emp_id")
    month = request.args.get("month")

    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)

    query = "SELECT * FROM google_form_response"
    conditions = []
    params = []

    if manager_name:
        conditions.append("manager_name = %s")
        params.append(manager_name)

    if emp_id:
        conditions.append("emp_id = %s")  # CORRECT
        params.append(emp_id)

    if month:
        conditions.append("MONTH(submitted_at) = %s")
        params.append(month)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    print("SQL:", query)
    print("Params:", params)

    responses = cursor.fetchall()
    cursor.close()
    db_conn.close()

    return jsonify({"success": True, "responses": responses})


from flask import request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode
import base64
@main_bp.route('/admin/create-user', methods=['POST'])
@nocache
def create_user():
    # 1️⃣  Read regular form fields
    emp_id      = request.form.get('emp_id')
    email       = request.form.get('email')
    name        = request.form.get('name')
    phoneno     = request.form.get('phoneno')
    designation = request.form.get('Designation')
    bloodgrp    = request.form.get('bloodgrp')
    doi         = request.form.get('doi')

    # 2️⃣  Read uploaded photo
    photo_file = request.files.get('photo')
    if not all([emp_id, email, name, phoneno,
                designation, bloodgrp, doi, photo_file]):
        return jsonify({'success': False,
                        'message': 'All fields (incl. photo) are required'}), 400

    try:
        # 3️⃣  Convert uploaded photo (stream) to PIL.Image
        emp_photo = Image.open(photo_file.stream).convert("RGB")

        # 4️⃣  Build the ID-card image in memory
        idcard_img = create_id_card({
            "Name":         name,
            "Designation":  designation,
            "Phone No.":    phoneno,
            "ID Card No":   f"{str(emp_id).zfill(3)}",
            "Photo":        emp_photo,
            "Blood Group":  bloodgrp,
            "Date of Joining": doi

        })

        # 5️⃣  Encode both images into PNG bytes
        buf_photo, buf_card = io.BytesIO(), io.BytesIO()
        emp_photo.save(buf_photo, format="PNG")
        idcard_img.save(buf_card, format="PNG")
        photo_bin, idcard_bin = buf_photo.getvalue(), buf_card.getvalue()

        # 6️⃣  Insert into DB
        db, cur = get_db(), None
        cur = db.cursor()
        sql = """
            INSERT INTO employees
            (emp_id, email, name, phoneno, designation,
             bloodgrp, doi, status, idcard)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'Active', %s)
        """
        cur.execute(sql, (emp_id, email, name, phoneno, designation,
                          bloodgrp, doi, idcard_bin))
        db.commit()
        return jsonify({'success': True})

    except Exception as err:
        if 'db' in locals(): db.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if 'cur' in locals() and cur: cur.close()

@main_bp.route("/admin/next-emp-id", methods=["GET"])
@nocache
def get_next_emp_id():
    db= get_db()
    cur = db.cursor()
    cur.execute("SELECT emp_id FROM employees WHERE emp_id LIKE 'SV_%' ORDER BY emp_id DESC LIMIT 1")
    last_id_row = cur.fetchone()
    cur.close()

    if last_id_row:
        try:
            last_num = int(last_id_row[0].split('_')[1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    emp_id = f"SV_{str(next_num).zfill(3)}"
    return jsonify({"emp_id": emp_id})

from werkzeug.utils import secure_filename


@main_bp.route('/admin/total-employees', methods=['GET'])
@nocache
def total_employees():
    try:
        emp_id = request.args.get("emp_id")
        email = request.args.get("email")

        db = get_db()
        cursor = db.cursor()

        query = "SELECT emp_id, email, status FROM employees WHERE 1=1"
        params = []

        if emp_id:
            query += " AND emp_id LIKE %s"
            params.append(f"%{emp_id}%")
        if email:
            query += " AND email LIKE %s"
            params.append(f"%{email}%")

        cursor.execute(query, tuple(params))
        employees = [{"emp_id": row[0], "email": row[1], "status": row[2]} for row in cursor.fetchall()]
        total = len(employees)
        cursor.close()

        return jsonify({"total": total, "employees": employees})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@main_bp.route('/admin/toggle-status', methods=['POST'])
@nocache
def toggle_employee():
    data = request.json
    emp_id = data.get("emp_id")
    new_status = data.get("status")

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE employees SET status = %s WHERE emp_id = %s", (new_status, emp_id))
        db.commit()
        cursor.close()
        return jsonify({"message": f"Employee {emp_id} is now {new_status}!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/get_form_visibility', methods=['GET'])
@nocache
def get_form_visibility():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT is_visible FROM form_visibility LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return jsonify({"success": True, "is_visible": row["is_visible"]})
        else:
            return jsonify({"success": False, "message": "No visibility record found."})
    except Exception as e:
        print("Error fetching visibility:", e)
        return jsonify({"success": False, "message": "Server error."})




@main_bp.route("/view_id")
def view_id():
    emp_id = session.get("emp_id")

    if not emp_id:
        return "Invalid Employee ID", 400

    db = get_db()
    cur = db.cursor()
    try:
        sql = "SELECT idcard FROM employees WHERE emp_id = %s"
        cur.execute(sql, (emp_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            return "Employee ID Card Not Found", 404

        idcard_bin = row[0]  # This is the binary data of the image

        img_io = io.BytesIO(idcard_bin)
        img_io.seek(0)

        return send_file(img_io, mimetype="image/png")

    except Exception as e:
        return f"Error fetching ID card: {str(e)}", 500

    finally:
        cur.close()


@main_bp.route('/upload_excel', methods=['POST'])
def upload_excel():
    import re

    def normalize(col):
        """Remove non-alphanumerics and lowercase the column name"""
        return re.sub(r'[^a-z0-9]', '', col.strip().lower())

    file = request.files.get('excel_file')
    filepath = None

    if not file or file.filename == '':
        return jsonify({'success': False, 'message': "No file selected."})

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'message': "Invalid file format. Please upload .xlsx or .xls file."})

    try:
        # Save file to server
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read file & clean up headers
        df = pd.read_excel(filepath, index_col=None)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Drop unnamed index/extra columns

        original_cols = df.columns.tolist()
        normalized_cols = [normalize(col) for col in original_cols]
        df.columns = normalized_cols  # Rename columns in DataFrame

        # Define expected column aliases
        expected_columns_aliases = {
            'reg_no': ['regno', 'registrationno', 'regnumber', 'regnum'],
            'owner': ['owner', 'ownername', 'vehicleowner'],
            'chassis_no': ['chassisno', 'chassisnumber', 'chassis'],
            'eng_no': ['engno', 'enginenumber', 'engineno'],
            'model': ['model', 'vehiclemodel', 'carmodel'],
            'product_branch': ['productbranch', 'branch', 'productbranch'],
            'flm': ['flm', 'flmname', 'fieldmanager'],
            'arg_number_loan': ['argnumberloan', 'loannumber', 'loanno', 'agrnoloan'],
            'bkt': ['bkt', 'bucket', 'bktstatus']
        }

        # Match normalized columns to expected fields
        column_mapping = {}
        for expected, aliases in expected_columns_aliases.items():
            for alias in aliases:
                if alias in normalized_cols:
                    column_mapping[expected] = alias
                    break

        # Check for missing fields
        missing = [field for field in expected_columns_aliases if field not in column_mapping]
        if missing:
            readable = ', '.join(missing)
            return jsonify({'success': False, 'message': f"Missing or incorrect columns: {readable}"})

        # Prepare data for insertion
        df.fillna('', inplace=True)
        final_columns = [column_mapping[field] for field in expected_columns_aliases]
        records = df[final_columns].values.tolist()

        # Insert into MySQL
        db = get_db()
        cursor = db.cursor()
        insert_query = """
            INSERT INTO cars (reg_no, owner, chassis_no, eng_no, model,
                              product_branch, flm, arg_number_loan, bkt)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, records)
        db.commit()

        return jsonify({'success': True, 'message': f"{cursor.rowcount} records inserted successfully."})

    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'message': f"Error inserting data: {str(e)}"})

    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)





@main_bp.route('/search', methods=['GET', 'POST'])
def search_car():
    if "emp_id" not in session:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for("main.employee_login"))

    if request.method == 'POST':
        reg_no_last4 = request.form.get('reg_no', '').strip()
        if len(reg_no_last4) != 4 or not reg_no_last4.isdigit():
            flash("Please enter exactly 4 digits of the registration number", "error")
            return redirect(url_for("main.search_car"))

        # Store the search in session (or pass as a query param)
        session['last_search'] = reg_no_last4
        return redirect(url_for("main.search_car"))

    # GET request
    cars = []
    search_performed = False
    reg_no_last4 = session.pop('last_search', None)

    if reg_no_last4:
        db = get_db()
        with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
            search_pattern = f"%{reg_no_last4}"
            cursor.execute("SELECT * FROM cars WHERE reg_no LIKE %s", (search_pattern,))
            cars = cursor.fetchall()
            search_performed = True

            if not cars:
                flash("No vehicles found matching your search criteria", "warning")

    return render_template('search_cars.html', cars=cars, search_performed=search_performed)
