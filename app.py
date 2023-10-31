import os
import random
import sys
import time
import json
from datetime import timedelta, datetime
import pyodbc
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from constants import http_status_codes, custom_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from loguru import logger

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://vyay-test.azurewebsites.net"], supports_credentials=True)

jwt = JWTManager(app)

SESSION_TIMEOUT = 3600  # 3600 seconds = 1 hour

# ----------------------------- Debug Logs Configuration -----------------------------
logger.add("debug.log", rotation="1 week", level="DEBUG")  # Writes logs to debug.log file
# logger.add(sys.stderr, level="DEBUG")  # Also outputs logs to the console for debugging

# ----------------------------- Session Configuration -----------------------------
app.config['SECRET_KEY'] = 'your_flask_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=SESSION_TIMEOUT)

# ----------------------------- JWT Configuration -----------------------------
app.config['JWT_SECRET_KEY'] = '\xe3\x94~\x80\xf0\x14\xe1Uu\x07\xef\xa9\t\x9d\xdfZ\xd1\xbcA\xb8\xd4x'  # Need to Change
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=120)
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


# ------------------------------- Debug Log API -------------------------------
# Reading Logs:
@app.route('/read-log', methods=['GET'])
def log_reader():
    current_path = os.getcwd()
    file_path = f'{current_path}\debug.log'
    try:
        with open(file_path, 'r') as file:
            file_content = file.read()
        return file_content, 200  # Return file content as the response
    except FileNotFoundError:
        return 'File not found', 404  # Return 404 if the file is not found


# ------------------------------- Authentication API --------------------------------
# LOGIN API
@app.route('/login', methods=['POST'])
def login():
    try:
        # Validation for the Connection on DB/Server
        # if not connection:
        #     custom_error_response = {
        #         "responseMessage": "Database Connection Error",
        #         "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
        #         "reason": "Failed to connect to the database. Please try again later."
        #     }
        #     # Return the custom error response with a 500 status code
        #     return jsonify(custom_error_response)

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
        # cursor.execute(qry, (email, pwd))
        user_data = cursor.execute(qry, (email, pwd)).fetchone()

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
        session['userType'] = user_data.user_type
        session['emailId'] = user_data.email_id
        session['employeeId'] = user_data.employee_id
        employee_name = user_data.employee_first_name + ' ' + user_data.employee_last_name

        # Return the tokens to the client
        response_data = {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Success",
            "data": {
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "username": employee_name,
                "emailId": user_data.email_id,
                "userType": user_data.user_type,
                "designation": user_data.employee_business_title,
                "employeeId": user_data.employee_id,
                "is_new": user_data.is_new,
                "organization": user_data.organization,
                "currency": user_data.employee_currency_code
            }
        }
        return jsonify(response_data)
    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong",
            "error": str(err)
        })


# REFRESH API
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    # existing_refresh_token = session.get('refreshToken')

    # # Session Validation
    # if existing_refresh_token is None:
    #     response_data = {
    #         "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
    #         "responseMessage": "Session Expired"
    #     }
    #     return jsonify(response_data)

    # # Get the Authorization header from the request
    # auth_header = request.headers.get('Authorization')
    # if auth_header is None:
    #     response_data = {
    #         "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
    #         "responseMessage": "Invalid Token Found"
    #     }
    #     return jsonify(response_data)
    #
    # # Taking Token from the Auth Header
    # auth_token = auth_header.split(" ")
    # if len(auth_token) != 2:
    #     response_data = {
    #         "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
    #         "responseMessage": "Invalid Token Found"
    #     }
    #     return jsonify(response_data)
    #
    # auth_token = auth_token[1]

    # # Validation of the Valid Refresh Token
    # if auth_token != existing_refresh_token:
    #     response_data = {
    #         "responseCode": http_status_codes.HTTP_401_UNAUTHORIZED,
    #         "responseMessage": "Invalid Token Found"
    #     }
    #     return jsonify(response_data)

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

            # # Validating the Session Variable
            # if 'emailId' not in session:
            #     session_response = {
            #         "responseMessage": "Session Expired !",
            #         "responseCode": custom_status_codes.expired_session
            #     }
            #     return jsonify(session_response)

            # email = session.get("emailId")
            email = data.get("emailId")
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
# 1. Request Common Data Insertion:
@app.route('/travel-request', methods=['GET', 'POST'])
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

    if request.method == 'GET':
        try:
            request_id = request.headers.get('requestId')

            # Validating request_id in travel Request Table:
            query = "SELECT request_id, request_name, request_policy, start_date, end_date, purpose, status FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, (request_id,))
            result = cursor.fetchone()
            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Not Exists!!"
                }
            else:
                column_names = ['request_id', 'request_name', 'request_policy', 'start_date', 'end_date', 'purpose',
                                'status']
                response_data = dict(zip(column_names, result))
                return {
                    "responseCode": http_status_codes.HTTP_200_OK,
                    "responseData": response_data,
                    'responseMessage': 'Travel Request Fetched Successfully'
                }
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong While Fetching Record",
                "reason": str(err)
            })

    elif request.method == 'POST':
        # Saving the Request Data
        try:
            data = request.get_json()
            if "organization" not in data or "employeeId" not in data:
                return {
                    "responseCode": 400,
                    "responseMessage": "(DEBUG) - Need Organization ID and Employee ID"
                }
            organization = data.get('organization')
            employee_id = data.get('employeeId')

            # Validating the Organization_ID already exist or not:
            query = "SELECT TOP 1 1 AS exists_flag FROM organization WHERE company_id = ?"
            cursor.execute(query, organization)
            result = cursor.fetchone()
            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Organization ID is Invalid!!"
                }

            # Validation of the required Fields:
            if "requestId" not in data or "requestName" not in data or "requestPolicy" not in data or "startDate" not in data or "endDate" not in data or "purpose" not in data:
                required_data = {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields Empty"
                }
                return jsonify(required_data)

            employee_id = employee_id
            organization = organization
            request_id = data.get('requestId')
            request_name = data.get('requestName')
            request_policy = data.get('requestPolicy')
            purpose = data.get('purpose')
            start_date = data.get('startDate')
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = data.get('endDate')
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            status = data.get('status')

            # Validating the Request_ID already exist or not:
            query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, request_id)
            result = cursor.fetchone()
            if result is not None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Already Exists!!"
                }

            sql_query = "INSERT INTO travelrequest (organization, user_id, request_id, request_name, request_policy, start_date, end_date, purpose, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(sql_query, organization, employee_id, request_id, request_name, request_policy, start_date,
                           end_date, purpose, status)
            connection.commit()

            return jsonify({"responseMessage": "Travel Request Saved", "responseCode": http_status_codes.HTTP_200_OK})
        except Exception as e:
            return jsonify({
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong",
                "reason": str(e)
            })


# 2. updating Cost Center
@app.route('/request-cost-center', methods=['GET', 'POST'])
@jwt_required()
def update_cost_center():
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    if request.method == "GET":
        try:
            request_id = request.headers.get('requestId')
            organization = request.headers.get('organization')
            employee = request.headers.get('employeeId')

            if organization is None or employee is None:
                return {
                    "responseCode": 400,
                    "responseMessage": "(DEBUG) -> employeeId and Organization are required field"
                }

            try:
                qry_1 = "SELECT u.employee_id, u.employee_first_name, u.employee_middle_name, u.employee_last_name, u.employee_business_title, u.costcenter, u.employee_country_name, u.employee_currency_code, u.employee_currency_name, u.manager_id, u.l1_manager_id, u.l2_manager_id, org.expense_administrator, org.finance_contact_person, org.company_name AS organization, bu.business_unit_name AS business_unit, d.department AS department, f.function_name AS func FROM userproc05092023_1 u LEFT JOIN organization org ON u.organization = org.company_id LEFT JOIN businessunit bu ON u.business_unit = bu.business_unit_id LEFT JOIN departments d ON bu.business_unit_id = d.business_unit LEFT JOIN functions f ON d.department = f.department WHERE u.employee_id = ?;"
                user_data = cursor.execute(qry_1, employee).fetchall()

                qry_2 = "SELECT cost_center FROM travelrequest WHERE request_id=?"
                cost_center = cursor.execute(qry_2, (request_id,)).fetchone()

            except Exception as err_1:
                return {
                    "error": str(err_1),
                    "responseCode": 500,
                    "responseMessage": "Error is Occurring"
                }

            task_list = [{'employee_id': user.employee_id,
                          'employee_first_name': user.employee_first_name,
                          'employee_middle_name': user.employee_middle_name,
                          'employee_last_name': user.employee_last_name,
                          'employee_business_title': user.employee_business_title,
                          'cost_center': user.costcenter,
                          'employee_country_name': user.employee_country_name,
                          'employee_currency_code': user.employee_currency_code,
                          'employee_currency_name': user.employee_currency_name,
                          'manager_id': user.manager_id,
                          'l1_manager_id': user.l1_manager_id,
                          'l2_manager_id': user.l2_manager_id,
                          'expense_administrator': user.expense_administrator,
                          'finance_contact_person': user.finance_contact_person,
                          'company_name': user.organization,
                          'business_unit': user.business_unit,
                          'department': user.department,
                          'function': user.func}
                         for user in user_data]

            if len(task_list) == 1:
                task_list = task_list[0]
                if cost_center is not None:
                    task_list["cost_center"] = cost_center
            else:
                task_list = None
            return jsonify({
                "responseCode": 200,
                "responseMessage": "Success",
                "data": task_list
            })

        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })

    if request.method == "POST":
        data = request.get_json()
        # Validation for the Connection on DB/Server
        try:
            if "requestId" not in data or "costCenter" not in data:
                return {
                    "responseCode": 400,
                    "responseMessage": "(DEBUG) - Need Request ID and Cost Center"
                }

            request_id = data.get('requestId')
            cost_center = data.get('costCenter')

            # Validating request_id in travel Request Table:
            query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, request_id)
            result = cursor.fetchone()
            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Not Exists!!"
                }

            # Validating Cost Center in Travel Request Tables:

            # Updating Cost Center in the request Table:
            query = f"UPDATE travelrequest SET cost_center=? WHERE request_id=?"
            cursor.execute(query, (cost_center, request_id))
            connection.commit()
            return jsonify({
                "responseMessage": "Cost Center Saved",
                "responseCode": http_status_codes.HTTP_200_OK
            })
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })


# 3. Request Transportation on Travel
@app.route('/request-transport', methods=['POST'])
# @jwt_required()
def request_transportation():
    try:
        data = request.get_json()
        print("connection: ", connection)
        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        # Validation of Data:
        if "requestId" not in data or "transports" not in data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        request_Id = data.get('requestId')
        transports = data.get('transports')

        # Validating the Request_ID already exist or not:
        query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
        cursor.execute(query, request_Id)
        result = cursor.fetchone()

        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request ID Not Exists!!"
            }

        for trans in transports:
            print("trans: ", trans)
            transport_type = trans['transportType']
            trip_type = trans['tripWay']

            # Get the ID of the inserted row
            sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
            cursor.execute(sql_query, (request_Id, transport_type, trip_type))

            # Get the ID of the inserted row
            cursor.execute("SELECT id from transport Where request_id=? and transport_type=? and trip_type=?")
            row_id = cursor.fetchone()

            connection.commit()
            print("trans: ", trans)
            print("New ID: ", row_id)

        # print("Transport(after adding requestId): ", transports)
        return jsonify({
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Hey All Good"
        })

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


# 4. Request Hotel on Travel
@app.route('/request-hotel', methods=['GET', 'POST'])
@jwt_required()
def request_hotel():
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    if request.method == "GET":
        try:
            request_id = request.headers.get('requestId')
            query = "SELECT * from hotel WHERE request_id=?"
            request_hotel_data = cursor.execute(query, request_id).fetchall()
            hotel_list = [{'requestId': hotel.request_id, 'cityName': hotel.city_name,
                           "startDate": hotel.check_in, "endDate": hotel.check_out,
                           "estimatedCost": hotel.estimated_cost} for hotel in
                          request_hotel_data]

            response_data = {
                "data": hotel_list,
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Hotel Request Successfully Fetched"
            }
            return jsonify(response_data)
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })

    if request.method == "POST":
        try:
            data = request.get_json()
            # Validation of Data:
            if "requestId" not in data or "hotels" not in data:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields are Empty"
                }

            # Validating request_id in travel Request Table:
            request_id = data.get("requestId")
            hotels = data.get("hotels")
            query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, request_id)
            result = cursor.fetchone()
            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Not Exists!!"
                }

            if len(hotels) < 0 or len(hotels) > 5:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "List of Hotels can be Min. 1 or Max. 5"
                }

            for hotel in hotels:
                hotel['requestId'] = request_id

            # Construct the SQL query for bulk insert
            values = ', '.join([
                f"('{hotel['cityName']}', '{hotel['startDate']}', '{hotel['endDate']}', {hotel['estimatedCost']}, '{hotel['requestId']}')"
                for hotel in hotels
            ])
            query = f"INSERT INTO hotel (city_name, check_in, check_out, estimated_cost, request_id) VALUES {values}"

            # Execute the query
            cursor.execute(query)
            connection.commit()

            return jsonify({
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Hotels Saved Successfully",
            })
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })


# 5. Request PerDiem on Travel
@jwt_required()
@app.route('/request-perdiem', methods=['GET', 'POST'])
def request_perdiem():
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    if request.method == "GET":
        try:
            request_id = request.headers.get("requestId")
            if request_id is None:
                return {
                    "responseCode": 400,
                    "responseMessage": "(Debug) -> requestId is required Field"
                }
            query = "SELECT * from perdiem WHERE request_id=?"
            request_perdiem_data = cursor.execute(query, (request_id,)).fetchall()

            per_diem_list = [
                {
                    'date': diem.diem_date,  # 'date': diem.diem_date.strftime('%d/%m/%Y'),
                    "breakfast": diem.breakfast,
                    "lunch": diem.lunch,
                    "dinner": diem.dinner
                }
                for diem in request_perdiem_data
            ]

            response_data = {
                "data": per_diem_list,
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Hotel Request Successfully Fetched"
            }
            return jsonify(response_data)
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })

    if request.method == "POST":
        try:
            data = request.get_json()
            # Validation of Data:
            if "requestId" not in data or "diems" not in data:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields are Empty"
                }

            request_id = data.get("requestId")
            diems = data.get("diems")

            # Validating request_id in travel Request Table:
            query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, request_id)
            result = cursor.fetchone()
            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Not Exists!!"
                }

            if "incident_expense" in data or "international_roaming" in data:
                international_roaming = data.get("international_roaming")
                incident_expense = data.get("incident_expense")

                query = f"UPDATE travelrequest SET international_roaming=?, incident_expense=? WHERE request_id=?"
                cursor.execute(query, (international_roaming, incident_expense, request_id))
                connection.commit()

            # Limit of the Diems (Max. 5)
            if len(diems) < 0 or len(diems) > 5:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "List of Hotels can be Min. 1 or Max. 5"
                }

            for diem in diems:
                diem['requestId'] = request_id

            # Construct the SQL query for bulk insert
            values = ', '.join([
                f"('{diem['date']}', '{diem['breakfast']}', '{diem['lunch']}', {diem['dinner']}, '{diem['requestId']}')"
                for diem in diems
            ])
            query = f"INSERT INTO perdiem (diem_date, breakfast, lunch, dinner, request_id) VALUES {values}"

            # Execute the query
            cursor.execute(query)
            connection.commit()

            return jsonify({
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Diems Saved Successfully",
            })
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })


# 6. Request Advance Cash on Travel
@app.route('/request-advcash', methods=['GET', 'POST'])
@jwt_required()
def request_advcash():
    # Validation for the Connection on DB/Server
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)
    if request.method == "GET":
        try:
            request_id = request.headers.get("requestId")
            if request_id is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "(DEBUG) -> RequestId is Required"
                }
            query = "SELECT cash_in_advance, reason_cash_in_advance FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, (request_id,))

            # Fetch the data
            cash_advance_data = cursor.fetchone()

            # Check if data is found
            if cash_advance_data:
                cash_in_advance, reason_cash_in_advance = cash_advance_data
            else:
                cash_in_advance = None
                reason_cash_in_advance = None

            response_data = {
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Cash Advance Data Fetched",
                "data": {
                    "cashInAdvance": cash_in_advance,
                    "reasonCashInAdvance": reason_cash_in_advance
                }
            }
            return jsonify(response_data)
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })

    if request.method == "POST":
        try:
            data = request.get_json()

            # Validation of Data:
            if "requestId" not in data or "cash_in_advance" not in data or "reason_cash_in_advance" not in data:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields are Empty"
                }

            request_id = data.get("requestId")
            cash_in_advance = data.get("cash_in_advance")
            reason_cash_in_advance = data.get("reason_cash_in_advance")

            # Query To Save Advance Cash Request in Travel Request Table
            query = f"UPDATE travelrequest SET cash_in_advance=?, reason_cash_in_advance=? WHERE request_id=?"
            cursor.execute(query, (cash_in_advance, reason_cash_in_advance, request_id))
            connection.commit()

            return jsonify({
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Cash Advance Saved Successfully",
            })

        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })


# ------------------------------- Request Status Update -------------------------------

@app.route('/request-submit', methods=['POST'])
@jwt_required()
def request_submit():
    try:
        data = request.get_json()

        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        # Validation of Required Data:
        if "requestId" not in data or "status" not in data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        request_id = data.get("requestId")
        status = data.get("status")

        # Validating request_id in travel Request Table:
        query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
        cursor.execute(query, request_id)
        result = cursor.fetchone()
        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request ID Not Exists!!"
            }
        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Request Submitted Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


@app.route('/manager-approve', methods=['POST'])
@jwt_required()
def request_approved():
    try:
        data = request.get_json()

        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        # Validation of Required Data:
        if "requestId" not in data or "status" not in data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        request_id = data.get("requestId")
        status = data.get("status")

        # Validating request_id in travel Request Table:
        query = "SELECT 1 AS exists_flag FROM travelrequest WHERE request_id = ? AND status = 'submitted'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        print("result: ", result)
        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Submitted to get Approve or Reject!!"
            }

        # Validation of the Value getting in the status Variable:
        # ...

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Request Approved Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


@app.route('/expense-admin-approve', methods=['POST'])
@jwt_required()
def request_sent_for_payment():
    try:
        data = request.get_json()

        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        # Validation of Required Data:
        if "requestId" not in data or "status" not in data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        request_id = data.get("requestId")
        status = data.get("status")

        # Validating request_id in travel Request Table:
        query = "SELECT 1 AS exists_flag FROM travelrequest WHERE request_id = ? AND status = 'approved'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        print("result: ", result)
        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Approved by Manager"
            }

        # Validation of the Value getting in the status Variable:
        # ...

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Request Send for Payment Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


@app.route('/finance-approve', methods=['POST'])
@jwt_required()
def request_paid():
    try:
        data = request.get_json()

        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            # Return the custom error response with a 500 status code
            return jsonify(custom_error_response)

        # Validation of Required Data:
        if "requestId" not in data or "status" not in data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        request_id = data.get("requestId")
        status = data.get("status")

        # Validating request_id in travel Request Table:
        query = "SELECT 1 AS exists_flag FROM travelrequest WHERE request_id = ? AND status = 'send for payment'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        print("result: ", result)
        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Approved from Expense Administrator"
            }

        # Validation of the Value getting in the status Variable:
        # ...

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Request Payment Made Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


# ------------------------------- Dashboard API -------------------------------
# Total Counts of Travel Requests
@app.route('/request-count', methods=["GET"])
@jwt_required()
def travel_request_count():
    try:
        # data = request.get_json()
        #
        # if "organization" not in data:
        #     return {
        #         "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
        #         "responseMessage": "(DEBUG) -> Organization is Required",
        #     }

        # organization = data.get('organization')

        query = """
                    SELECT
                        COUNT(*) AS total_requests,
                        SUM(CASE WHEN status IN ('rejected', 'initiated') THEN 1 ELSE 0 END) AS initiated_or_rejected_requests,
                        SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) AS submitted_requests
                    FROM travelrequest;
                """
        cursor.execute(query)

        # Fetch the results
        result = cursor.fetchone()

        # Store results in variables
        total_requests = result[0]
        initiated_or_rejected_requests = result[1]
        submitted_requests = result[2]

        # Create a response dictionary
        response = {
            'responseCode': 200,
            'data': {
                'totalRequests': total_requests,
                'openRequests': initiated_or_rejected_requests,
                'pendingRequest': submitted_requests
            }
        }
        return response

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


# Total Request of specific Employee:
@app.route('/total-travel-request', methods=['GET'])
@jwt_required()
def total_travel_request():
    try:
        employeeId = request.headers.get('employeeId')
        query = "SELECT * FROM travelrequest WHERE employee_id=?"
        result = cursor.execute(query, (employeeId, )).fetchall()
        total_travel_request_list = [
            {
                "requestId": req.request_id,
                "requestName": req.request_name,
                "requestPolicy": req.request_policy,
                "startDate": req.company_contact_name
            }
            for req in result
        ]

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Total Travel Request List",
            "data": total_travel_request_list
        }
    except Exception as err:
        return {
            "error": str(err),
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong"
        }


# Pending Request of specific Employee:
@app.route('/pending-travel-request', methods=['GET'])
@jwt_required()
def pending_travel_request():
    if not connection:
        custom_error_response = {
            "connection": str(connection),
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        return jsonify(custom_error_response)
    if request.method == "GET":
        try:
            employeeId = request.headers.get('employeeId')
            query = "SELECT * FROM travelrequest WHERE status=submitted and employee_id=?"
            total_travel_request_data = cursor.execute(query, (employeeId,)).fetchall()
            task_list = [
                {
                    "requestId": req.request_id,
                    "requestName": req.request_name,
                    "requestPolicy": req.request_policy,
                    "startDate": req.company_contact_name
                }
                for req in total_travel_request_data
            ]
            return jsonify(task_list)
        except Exception as err:
            return {
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong",
                "error": str(err)
            }


# Open Request of specific Employee:
@app.route('/open-travel-request', methods=['GET'])
@jwt_required()
def open_travel_request():
    if not connection:
        custom_error_response = {
            "connection": str(connection),
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        return jsonify(custom_error_response)

    if request.method == "GET":
        try:
            employeeId = request.headers.get('employeeId')
            query = "SELECT * FROM travelrequest WHERE status=initiated or status=rejected and employee_id=?"
            total_travel_request_data = cursor.execute(query, (employeeId, )).fetchall()
            task_list = [
                {
                    "requestId": req.request_id,
                    "requestName": req.request_name,
                    "requestPolicy": req.request_policy,
                    "startDate": req.company_contact_name
                }
                for req in total_travel_request_data
            ]
            return jsonify(task_list)
        except Exception as err:
            return {
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong",
                "error": str(err)
            }


# ------------------------------- Data Fetch API -------------------------------
@app.route('/get-organization', methods=['GET'])
def get_org():
    try:
        # Validation for the Connection on DB/Server
        if not connection:
            custom_error_response = {
                "connection": str(connection),
                "responseMessage": "Database Connection Error",
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "reason": "Failed to connect to the database. Please try again later."
            }
            return jsonify(custom_error_response)
        qry = f"SELECT * FROM organization"
        organization_data = cursor.execute(qry).fetchall()
        task_list = [{'Company Name': org.company_name, 'Company Onboard Date': org.company_onboard_date,
                      "Company ID": org.company_id, "Company Contact Name": org.company_contact_name} for org in
                     organization_data]
        return jsonify(task_list)
    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


# Get Request_policy Data:
@app.route('/get-request-policy', methods=['GET'])
@jwt_required()
def get_request_policy():
    try:
        organization = request.headers.get('organization')
        if organization is None:
            return {
                "responseMessage": "(DEBUG) -> Organization is Required Field",
                "responseCode": 400
            }

        qry = f"SELECT * FROM requestpolicy where organization=?"
        request_policy_data = cursor.execute(qry, organization).fetchall()
        task_list = [{"label": policy.request_policy_name,
                      "perDiem": bool(policy.perdiem),
                      "cashAdvance": bool(policy.cashadvance),
                      "internationRoaming": bool(policy.international_roaming),
                      "incidentCharges": bool(policy.incident_charges)
                      } for policy in request_policy_data]
        return jsonify({"responseCode": 200,
                        "data": task_list,
                        "responseMessage": "Request Policy Successfully Fetched!!!"})

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


# Get General/Profile Data:
@app.route('/get-profile', methods=['GET'])
def get_profile():
    organization = request.headers.get('organization')
    employee = request.headers.get('employeeId')

    print("connection: ", connection)

    if organization is None or employee is None:
        return {
            "responseCode": 400,
            "responseMessage": "(DEBUG) -> employeeId and Organization are required field"
        }

    # Validating the organizationId and employeeId

    qry = """
            SELECT 
            u.employee_id,
            u.employee_first_name,
            u.employee_middle_name,
            u.employee_last_name,
            u.employee_business_title,
            u.costcenter,
            u.employee_country_name,
            u.employee_currency_code,
            u.employee_currency_name,
            u.manager_id,
            u.l1_manager_id,
            u.l2_manager_id,
            org.expense_administrator,
            org.finance_contact_person,
            org.company_name AS organization,
            bu.business_unit_name AS business_unit,
            d.department AS department,
            f.function_name AS func
        FROM 
            userproc05092023_1 u
        LEFT JOIN 
            organization org ON u.organization = org.company_id
        LEFT JOIN 
            businessunit bu ON u.business_unit = bu.business_unit_id
        LEFT JOIN 
            departments d ON bu.business_unit_id = d.business_unit
        LEFT JOIN 
            functions f ON d.department = f.department
        WHERE 
            u.employee_id = ?;
    """
    try:
        qry_1 = "SELECT u.employee_id, u.employee_first_name, u.employee_middle_name, u.employee_last_name, u.employee_business_title, u.costcenter, u.employee_country_name, u.employee_currency_code, u.employee_currency_name, u.manager_id, u.l1_manager_id, u.l2_manager_id, org.expense_administrator, org.finance_contact_person, org.company_name AS organization, bu.business_unit_name AS business_unit, d.department AS department, f.function_name AS func FROM userproc05092023_1 u LEFT JOIN organization org ON u.organization = org.company_id LEFT JOIN businessunit bu ON u.business_unit = bu.business_unit_id LEFT JOIN departments d ON bu.business_unit_id = d.business_unit LEFT JOIN functions f ON d.department = f.department WHERE u.employee_id = ?;"
        user_data = cursor.execute(qry_1, employee).fetchall()

    except Exception as err_1:
        return {
            "error": str(err_1),
            "responseCode": 500,
            "responseMessage": "Error is Occurring"
        }

    task_list = [{'employee_id': user.employee_id,
                  'employee_first_name': user.employee_first_name,
                  'employee_middle_name': user.employee_middle_name,
                  'employee_last_name': user.employee_last_name,
                  'employee_business_title': user.employee_business_title,
                  'cost_center': user.costcenter,
                  'employee_country_name': user.employee_country_name,
                  'employee_currency_code': user.employee_currency_code,
                  'employee_currency_name': user.employee_currency_name,
                  'manager_id': user.manager_id,
                  'l1_manager_id': user.l1_manager_id,
                  'l2_manager_id': user.l2_manager_id,
                  'expense_administrator': user.expense_administrator,
                  'finance_contact_person': user.finance_contact_person,
                  'company_name': user.organization,
                  'business_unit': user.business_unit,
                  'department': user.department,
                  'function': user.func}
                 for user in user_data]
    if len(task_list) == 1:
        task_list = task_list[0]
    else:
        task_list = None
    return jsonify({
        "responseCode": 200,
        "responseMessage": "Success",
        "data": task_list
    })


if __name__ == '__main__':
    app.run(debug=True)
