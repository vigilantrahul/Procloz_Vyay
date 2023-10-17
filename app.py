import random
import sys
import time
from datetime import timedelta
import pyodbc
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from constants import http_status_codes, custom_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://vyay-test.azurewebsites.net"], supports_credentials=True)

jwt = JWTManager(app)

# ----------------------------- Session Configuration -----------------------------
app.config['SECRET_KEY'] = 'your_flask_secret_key'

# ----------------------------- JWT Configuration -----------------------------
app.config[
    'JWT_SECRET_KEY'] = '\xe3\x94~\x80\xf0\x14\xe1Uu\x07\xef\xa9\t\x9d\xdfZ\xd1\xbcA\xb8\xd4x'  # Need to Change
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_ALGORITHM'] = 'HS256'  # HMAC with SHA-256


# Custom response for expired tokens
@jwt.expired_token_loader
def expired_token_callback(arg1, arg2):
    return jsonify({'responseMessage': 'Token has expired',
                    'responseCode': custom_status_codes.expired_token})


# Custom response for invalid tokens
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'responseMessage': 'Invalid token',
        'responseCode': custom_status_codes.invalid_token
    })


# ----------------------------- SERVER Configuration -----------------------------
def establish_db_connection():
    try:
        server_name = 'ibproproclozdbserver.database.windows.net'
        database_name = 'Procloz_vyay'
        username = 'dbadmin'
        password = 'NPY402OYM5GUHBW2$'

        connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server_name};Database={database_name};UID={username};PWD={password}"
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        return connection, cursor
    except pyodbc.Error as err:
        error_message = str(err)
        return None, error_message


# Called to get the Objects
connection, cursor = establish_db_connection()

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
    print(connection)
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

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

    session['userId'] = user_id
    session['organization'] = user_data.organization
    session['accessToken'] = access_token
    session['refreshToken'] = refresh_token
    session['username'] = user_data.employee_name
    session['userType'] = user_data.user_type
    session['emailId'] = user_data.email_id
    session['employeeId'] = user_data.employee_id

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
            "employeeId": user_data.employee_id,
            "is_new": user_data.is_new
        }
    }
    return jsonify(response_data)


# REFRESH API
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    existing_refresh_token = session.get('refreshToken')

    # Session Validation
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
    session['access_Token'] = new_access_token
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
    print(connection)
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

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
    req_otp = int(req_otp)

    query = "SELECT otp, otp_created_at FROM userproc05092023_1 WHERE email_id=?"
    cursor.execute(query, email)
    result = cursor.fetchone()

    if result is None:
        return {"responseCode": http_status_codes.HTTP_401_UNAUTHORIZED, "responseMessage": "Invalid Email Found"}

    otp, otp_created_at = result
    current_time = int(time.time())
    remaining_time = (current_time - otp_created_at)

    if otp != req_otp or remaining_time >= 300:  # Checking here for Right OTP and Under the valid Timing
        return {"responseCode": http_status_codes.HTTP_401_UNAUTHORIZED, "responseMessage": "Invalid OTP Found"}
    else:
        return {"responseCode": http_status_codes.HTTP_200_OK, "responseMessage": "OTP Verified"}


# RESET PASSWORD
@app.route('/reset-password', methods=['POST'])
def reset_password():
    print(connection)
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

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
    try:
        print(connection)
        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        try:
            data = request.get_json()
            # required Fields Validation
            if len(data) == 0:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields are Empty"
                }
        except Exception as err1:
            return {
                "responseCode": 500,
                "responseMessage": "Something Went Wrong 1",
                "error": str(err1)
            }

        try:
            req_old_password = data.get('oldPassword', '')
            new_password = data.get('newPassword', '')

            # Validating the Required Fields
            if req_old_password == '' or new_password == '':
                return {
                    "responseCode": 500,
                    "responseMessage": "Required Field is Empty"
                }

            # Validating the Session Variable
            if 'emailId' not in session:
                session_response = {
                    "responseMessage": "Session Expired !",
                    "responseCode": custom_status_codes.expired_session
                }
                return jsonify(session_response)

            email = session.get("emailId")
            query = 'SELECT password, is_new from userproc05092023_1 WHERE email_id=?'
            cursor.execute(query, email)
            result = cursor.fetchone()
            if result is not None:
                old_password, is_new = result
        except Exception as err2:
            return {
                "responseCode": 500,
                "responseMessage": "Something Went 2",
                "error": str(err2)
            }

        try:
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
        except Exception as err3:
            return {
                "responseCode": 500,
                "responseMessage": "Something Went Wrong 3",
                "error": str(err3)
            }
    except Exception as e:
        return {
            "responseCode": 500,
            "responseMessage": "Something Went Wrong",
            "error": str(e)
        }


# ------------------------------- Request Initiating API -------------------------------
# Request Common Data Insertion:
@app.route('/travel-request', methods=['POST'])
@jwt_required()
def request_initiate():
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    # Verifying Session:
    if "organization" not in session or "employeeId" not in session:
        print("Session Expired !!")
        session_response = {
            "responseMessage": "Session Expired !",
            "responseCode": custom_status_codes.expired_session
        }
        return jsonify(session_response)

    # Saving the Request Data
    try:
        data = request.get_json()
        employee_id = session.get('employeeId')
        organization = session.get('organization')
        request_id = data.get('requestId')
        request_name = data.get('requestName')
        request_policy = data.get('requestPolicy')
        start_date = data.get('startDate')
        end_date = data.get('endDate')

        sql_query = "INSERT INTO travelrequest (organization, user_id, request_id, request_name, request_policy, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)"

        cursor.execute(sql_query, organization, employee_id, request_id, request_name, request_policy, start_date,
                       end_date)
        connection.commit()

        return jsonify({"Message": "Success"})
    except Exception as e:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(e)
        })


# ------------------------------- Data Fetch API -------------------------------
@app.route('/get-organization', methods=['GET'])
def get_org():
    print(connection)
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    qry = f"SELECT * FROM organization"
    cursor.execute(qry)
    organization_data = cursor.fetchall()
    task_list = [{'Company Name': org.company_name, 'Company Onboard Date': org.company_onboard_date,
                  "Company Id": org.company_id, "Company Contact Name": org.company_contact_name} for org in
                 organization_data]
    return jsonify(task_list)


if __name__ == '__main__':
    app.run(debug=True)
