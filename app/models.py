from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(6))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class GoogleFormResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), nullable=False)
    manager_name = db.Column(db.String(255), nullable=False)
    response_data = db.Column(db.JSON, nullable=False)  # Store responses as JSON
    submission_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "manager_name": self.manager_name,
            "response_data": self.response_data,
            "submission_date": self.submission_date.strftime('%Y-%m-%d %H:%M:%S')
        }
