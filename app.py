import random
import sys
import time
from datetime import timedelta
import pyodbc
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, session
from constants import http_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)
jwt = JWTManager(app)

# ----------------------------- Session Configuration -----------------------------
app.config['SECRET_KEY'] = 'your_flask_secret_key'

# ----------------------------- JWT Configuration -----------------------------
app.config['JWT_SECRET_KEY'] = 'your_secret_key'  # Change this to a secure random secret key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_ALGORITHM'] = 'HS256'  # HMAC with SHA-256

# ----------------------------- SERVER Configuration -----------------------------
server_name = 'ibproproclozdbserver.database.windows.net'
database_name = 'Procloz_vyay'
username = 'dbadmin'
password = 'NPY402OYM5GUHBW2$'

connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server_name};Database={database_name};UID={username};PWD={password}"
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

sys.path.append('/opt/startup/app_logs')
sys.path.append('/tmp/8dbb3862660c8b6/antenv/lib/python3.9/site-packages')

# ------------------------------- EMAIL Configuration -------------------------------
app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mverma@procloz.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'Ruv14930'  # Replace with your email password

mail = Mail(app)


# ------------------------------- Authentication API --------------------------------
# LOGIN API
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', '')
    pwd = request.json.get('password', '')

    if email == '' or pwd == '':
        response_data = {
            "response_code": http_status_codes.HTTP_400_BAD_REQUEST,
            "message": "Invalid Credentials Found !!!"
        }
        return jsonify(response_data)

    # Execute the SQL query to check user credentials
    qry = f"SELECT * FROM userproc05092023_1 WHERE email_id = '{email}' AND password = '{pwd}'"
    cursor.execute(qry)
    user_data = cursor.fetchone()

    if user_data is None:
        response_data = {
            "message": "Invalid email or password",
            "response_code": http_status_codes.HTTP_401_UNAUTHORIZED
        }
        return jsonify(response_data)

    # Get the user id from the user data obtained from the query
    user_id = user_data.id  # assuming id is the column name for user id in your database

    # Create access token
    access_token = create_access_token(identity=user_id)

    # Create refresh token (optional)
    refresh_token = create_refresh_token(identity=user_id)

    # Set session expiration time (30 minutes from now)
    session['session_expiration'] = time.time() + 30 * 60

    session['user_id'] = user_id
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    session['username'] = user_data.employee_name
    session['user_type'] = user_data.user_type

    # Return the tokens to the client
    response_data = {
        "response_code": http_status_codes.HTTP_200_OK,
        "response_message": "Success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": user_data.employee_name,
            "user_type": user_data.user_type,
            "designation": user_data.employee_business_title,
            "employee_id": user_data.employee_id
        }
    }
    return jsonify(response_data)


# REFRESH API
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # Get the Authorization header from the request
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        response_data = {
            "response_code": http_status_codes.HTTP_401_UNAUTHORIZED,
            "response_message": "Invalid Token Found"
        }
        return jsonify(response_data)

    # Taking Token from the Auth Header
    auth_token = auth_header.split(" ")
    if len(auth_token) != 2:
        response_data = {
            "response_code": http_status_codes.HTTP_401_UNAUTHORIZED,
            "response_message": "Invalid Token Found"
        }
        return jsonify(response_data)

    auth_token = auth_token[1]
    existing_refresh_token = session.get('refresh_token')

    # Validation of the Valid Refresh Token
    if auth_token != existing_refresh_token:
        response_data = {
            "response_code": http_status_codes.HTTP_401_UNAUTHORIZED,
            "response_message": "Invalid Token Found"
        }
        return jsonify(response_data)

    # Taking Identity From the Refresh Token
    current_user = get_jwt_identity()

    # Create a new access token
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)

    session['access_token'] = new_access_token
    session['refresh_token'] = new_refresh_token

    # Return the new access token to the client
    response_data = {
        "response_code": http_status_codes.HTTP_200_OK,
        "response_message": "Success",
        "data": {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    }
    return jsonify(response_data)


# Generate a 4-digit OTP
def generate_otp():
    return random.randint(1000, 9999)


# FORGET PASSWORD API
@app.route('/forget-password', methods=['POST'])
def forgot_password():
    print("Called Method")
    data = request.get_json()
    email = data.get('email', '')

    if email == '':
        return jsonify(error='Email found Blank')

    # Check if the email exists in the database
    cursor.execute(f"SELECT * FROM userproc05092023_1 WHERE email_id='{email}'")
    user = cursor.fetchone()

    if user:
        # Generate a new OTP
        otp = generate_otp()
        print(otp)

        # Store the OTP in the database (assuming you have an 'otp' column)
        cursor.execute(f"UPDATE userproc05092023_1 SET otp={otp} WHERE email_id='{email}'")
        connection.commit()

        sender_email = ""

        # Send the OTP to the user's email (implement your email sending logic here)
        msg = Message('OTP for Password Reset', sender=sender_email, recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)

        return jsonify(message='OTP sent to your email'), 200
    else:
        return jsonify(error='Email not found'), 404


# Database logic for verifying OTP and updating password (you need to implement this)
def verify_otp_and_reset_password(email, otp, new_password):
    # Verify OTP and reset the user's password in the database
    # Implement your database logic here
    # Return True if OTP is valid and password is successfully reset, else return False
    return True  # Placeholder, replace with your logic


# RESET PASSWORD
@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.json.get('email', '')
    otp = request.json.get('otp', '')
    new_password = request.json.get('new_password', '')
    sender_email = "mverma@procloz.com"
    # Verify OTP and reset password
    if verify_otp_and_reset_password(email, otp, new_password):
        # Password successfully reset, you can send a confirmation email if needed
        # Send password reset confirmation email to the user
        msg = Message('Password Reset Confirmation', sender=sender_email, recipients=[email])
        msg.body = 'Your password has been successfully reset.'
        mail.send(msg)

        return jsonify(message='Password reset successful'), 200
    else:
        return jsonify(error='Invalid OTP or email'), 401


# ------------------------------- Data Fetch API -------------------------------
@app.route('/get-org', methods=['GET'])
def get_org():
    qry = f"SELECT * FROM organization"
    cursor.execute(qry)
    organization_data = cursor.fetchall()
    task_list = [{'Company Name': org.company_name, 'Company Onboard Date': org.company_onboard_date,
                  "Company Id": org.company_id, "Company Contact Name": org.company_contact_name} for org in
                 organization_data]
    return jsonify(task_list)


if __name__ == '__main__':
    app.run(debug=True)
