import random
import sys
import time
from datetime import timedelta
import pyodbc
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from constants import http_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://vyay-test.azurewebsites.net"], supports_credentials=True)

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
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Invalid Credentials Found !!!"
        }
        return jsonify(response_data)

    # Execute the SQL query to check user credentials
    qry = f"SELECT * FROM userproc05092023_1 WHERE email_id=? AND password=?"
    cursor.execute(qry, (email, pwd))
    user_data = cursor.fetchone()

    if user_data is None:
        response_data = {
            "responseMessage": "Invalid email or password",
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED
        }
        return jsonify(response_data)

    # Get the user id from the user data obtained from the query
    user_id = user_data.id  # assuming id is the column name for user id in your database

    # Create access token
    access_token = create_access_token(identity=user_id)

    # Create refresh token
    refresh_token = create_refresh_token(identity=user_id)

    # Set session expiration time (30 minutes from now)
    session['session_expiration'] = time.time() + 30 * 60

    session['user_id'] = user_id
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token
    session['username'] = user_data.employee_name
    session['user_type'] = user_data.user_type
    session['email_id'] = user_data.email_id

    # Return the tokens to the client
    response_data = {
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Success",
        "data": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "username": user_data.employee_name,
            "userType": user_data.user_type,
            "designation": user_data.employee_business_title,
            "employeeId": user_data.employee_id
        }
    }
    return jsonify(response_data)


# REFRESH API
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # Session Validation
    existing_refresh_token = session.get('refresh_token')
    if existing_refresh_token is None:
        response_data = {
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
            "responseMessage": "Session Expired"
        }
        return jsonify(response_data)

    # Get the Authorization header from the request
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        response_data = {
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
            "responseMessage": "Invalid Token Found"
        }
        return jsonify(response_data)

    # Taking Token from the Auth Header
    auth_token = auth_header.split(" ")
    if len(auth_token) != 2:
        response_data = {
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
            "responseMessage": "Invalid Token Found"
        }
        return jsonify(response_data)

    auth_token = auth_token[1]

    # Validation of the Valid Refresh Token
    if auth_token != existing_refresh_token:
        response_data = {
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
            "responseMessage": "Invalid Token Found"
        }
        return jsonify(response_data)

    # Taking Identity From the Refresh Token
    current_user = get_jwt_identity()

    # Create a new access token
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)

    session['accessToken'] = new_access_token
    session['refreshToken'] = new_refresh_token

    # Return the new access token to the client
    response_data = {
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Success",
        "data": {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token
        }
    }
    return jsonify(response_data)


# Generate a 4-digit OTP
def generate_otp():
    return random.randint(1000, 9999)


# FORGET PASSWORD API
@app.route('/forget-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '')

    if email == '':
        return jsonify(error='Email found Blank')

    # Check if the email exists in the database
    query = "SELECT * FROM userproc05092023_1 WHERE email_id=?"
    cursor.execute(query, email)
    user = cursor.fetchone()

    response_data = {}
    if user:
        # Generate a new OTP
        otp = generate_otp()

        # Timing When OTP got Created
        current_time = time.time()

        # Store the OTP in the database
        query = "UPDATE userproc05092023_1 SET otp=?, otp_created_at=? WHERE email_id=?"
        cursor.execute(query, (otp, current_time, email))
        connection.commit()
        sender_email = "mverma@procloz.com"

        # Send the OTP to the user's email
        msg = Message('OTP for Password Reset', sender=sender_email, recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)
        response_data["responseMessage"] = 'OTP sent to your email'
        response_data["responseCode"] = http_status_codes.HTTP_200_OK

        return jsonify(response_data)
    else:
        response_data["responseMessage"] = 'Invalid Email Found'
        response_data["responseCode"] = http_status_codes.HTTP_404_NOT_FOUND

        return jsonify(response_data)


# Database logic for verifying OTP and updating password
@app.route('/otp-verify', methods=['POST'])
def verify_otp_code():
    data = request.json
    req_otp = data.get('otp', '')
    email = data.get('email', '')

    query = "SELECT otp, otp_created_at FROM userproc05092023_1 WHERE email_id=?"
    cursor.execute(query, email)
    result = cursor.fetchone()

    if result is None:
        return False

    otp, otp_created_at = result
    current_time = int(time.time())
    remaining_time = (current_time - otp_created_at)

    if otp != req_otp or remaining_time >= 10:  # Checking here for Right OTP and Under the valid Timing
        return False
    else:
        return True


# RESET PASSWORD
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json

    # required Fields Validation
    if len(data) == 0:
        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Required Fields are Empty"
        }

    email = data.get('email', '')
    new_password = data.get('new_password', '')
    sender_email = "mverma@procloz.com"

    if email == '' or new_password == '':
        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Required Fields are Empty"
        }

    # Store the OTP in the database (assuming you have an 'otp' column)
    query = f"UPDATE userproc05092023_1 SET password=?, otp=NULL, otp_created_at=NULL WHERE email_id=?"
    cursor.execute(query, (new_password, email))
    connection.commit()

    # Sending Email for Password Update Successfully
    msg = Message('Password Reset Confirmation', sender=sender_email, recipients=[email])
    msg.body = 'Your password has been successfully reset.'
    mail.send(msg)
    response_data = {
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Password Reset Successfully"
    }
    return jsonify(response_data)


# PASSWORD CHANGE
@app.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.json

    # required Fields Validation
    if len(data) == 0:
        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Required Fields are Empty"
        }

    req_old_password = data.get('oldPassword', '')
    new_password = data.get('newPassword', '')
    email = session.get("email_id")

    query = 'SELECT password, is_new from userproc05092023_1 WHERE email_id=?'
    cursor.execute(query, email)
    result = cursor.fetchone()
    old_password, is_new = result

    # Validation of the Old Password
    if old_password != req_old_password:
        return jsonify({
            "responseMessage": "Invalid old Password Found",
            "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED
        })

    # To Check is the User New or Old
    if is_new == 1:
        # Update Password
        query = f"UPDATE userproc05092023_1 SET password=?, is_new=0 WHERE email_id=?"
    else:
        # Update Password
        query = f"UPDATE userproc05092023_1 SET password=? WHERE email_id=?"
    cursor.execute(query, (new_password, email))
    connection.commit()

    response_data = {
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Password Changed Successfully"
    }
    return jsonify(response_data)


# ------------------------------- Data Fetch API -------------------------------
@app.route('/get-organization', methods=['GET'])
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
