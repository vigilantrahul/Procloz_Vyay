import os
import random
import sys
import time
from datetime import timedelta, datetime, date
import pyodbc
from flask_mail import Mail, Message
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from constants import http_status_codes, custom_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from loguru import logger
from TransportApi import flight_data, train_data, bus_data, taxi_data, carrental_data, clear_hotel_data, \
    clear_perdiem_data, clear_transport_data

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
app.config['MAIL_USERNAME'] = 'noreply@vyay.tech'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'BGweq589'  # Replace with your email password

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
        sender_email = "noreply@vyay.tech"

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
    sender_email = "noreply@vyay.tech"

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

        data = request.get_json()
        # required Fields Validation
        if len(data) == 0:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Required Fields are Empty"
            }

        req_old_password = data.get('oldPassword', '')
        new_password = data.get('newPassword', '')

        # Validating the Required Fields
        if req_old_password == '' or new_password == '':
            return {
                "responseCode": 500,
                "responseMessage": "Required Field is Empty"
            }

        email = data.get("emailId")
        print()
        query = 'SELECT password, is_new from userproc05092023_1 WHERE email_id=?'
        cursor.execute(query, email)
        result = cursor.fetchone()

        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Check the Email ID it's Invalid !!!"
            }

        old_password, is_new = result

        # Validation of the Old Password
        if old_password.casefold() != req_old_password.casefold():
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
                response_data = {
                    "requestId": response_data["request_id"],
                    "requestName": response_data["request_name"],
                    "requestPolicy": response_data["request_policy"],
                    "startDate": response_data["start_date"],
                    "endDate": response_data["end_date"],
                    "purpose": response_data["purpose"],
                    "status": response_data["status"]
                }
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

            # Code for the Updating Request Data on that particular request id
            if result is not None:
                sql_query = "UPDATE travelrequest SET organization = ?, user_id = ?, request_name = ?, request_policy = ?, start_date = ?, end_date = ?, purpose = ?, status = ? WHERE request_id = ?"
                cursor.execute(sql_query, organization, employee_id, request_name, request_policy, start_date, end_date,
                               purpose, status, request_id)
                connection.commit()

                return {
                    "responseCode": http_status_codes.HTTP_200_OK,
                    "responseMessage": "Request Data Updated Successfully!!"
                }

            # Query To Insert Data in the Request Table:
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
                # print("User_data: ", user_data)

                qry_2 = "SELECT cost_center FROM travelrequest WHERE request_id=?"
                cost_center = cursor.execute(qry_2, (request_id,)).fetchone()
                # print("Cost Center: ", cost_center)

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
                if cost_center[0] is not None:
                    task_list["cost_center"] = cost_center[0]
            else:
                task_list = None

            print("Task List if any change: ", task_list)
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
@app.route('/request-transport', methods=['GET', 'POST'])
@jwt_required()
def request_transportation():
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
            request_id = request.headers.get("requestId")  # Request ID for getting data

            # Execute raw SQL query to fetch data from transport and its related data from transporttripmapping
            query = """
                SELECT 
                    transport.transport_type,
                    transport.trip_type,
                    transporttripmapping.trip_from,
                    transporttripmapping.trip_to,
                    transporttripmapping.departure_date,
                    transporttripmapping.estimated_cost,
                    transporttripmapping.from_date,
                    transporttripmapping.to_date,
                    transporttripmapping.comment
                FROM transport
                LEFT JOIN transporttripmapping ON transport.id = transporttripmapping.transport
                WHERE transport.request_id = ?
            """

            cursor.execute(query, (request_id,))

            # Fetch results
            results = cursor.fetchall()
            transport_data = []
            current_transport = None

            # Inside the for loop where you process query results
            for row in results:
                transport_type, trip_type, *trip_mapping_data = row

                # Check if it's a new transport entry
                if not current_transport or transport_type != current_transport['transportType'] or trip_type != \
                        current_transport['tripType']:

                    if current_transport:
                        transport_data.append(current_transport)
                    current_transport = {
                        'transportType': transport_type,
                        'tripType': trip_type,
                        'trips': []
                    }

                if current_transport["transportType"] == "bus" or current_transport["transportType"] == "flight" or \
                        current_transport["transportType"] == "train":
                    # Add trip mapping data to the current transport entry
                    if trip_mapping_data:
                        trip_mapping = {
                            'from': trip_mapping_data[0],
                            'to': trip_mapping_data[1],
                            'departureDate': trip_mapping_data[2],
                            'estimateCost': trip_mapping_data[3]
                        }
                        current_transport['trips'].append(trip_mapping)

                elif current_transport["transportType"] == "taxi":
                    current_transport["estimateCost"] = trip_mapping_data[3]
                    current_transport["comment"] = trip_mapping_data[6]
                    del current_transport["tripType"]
                    del current_transport["trips"]

                elif current_transport["transportType"] == "carRental":
                    current_transport["estimateCost"] = trip_mapping_data[3]
                    current_transport["startDate"] = trip_mapping_data[4]
                    current_transport["endDate"] = trip_mapping_data[5]
                    current_transport["comment"] = trip_mapping_data[6]
                    del current_transport["tripType"]
                    del current_transport["trips"]

            # Add the last transport entry to the list:
            if current_transport:
                transport_data.append(current_transport)

            return jsonify(
                {
                    'data': transport_data,
                    'responseMessage': "Transport Data Fetch Successfully",
                    'responseCode': http_status_codes.HTTP_200_OK
                }
            )

        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })

    if request.method == "POST":
        try:
            data = request.get_json()
            transport_type = request.args.get('transportType')

            # Validation of None Value
            if transport_type is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Choose Valid Transport Type"
                }

            # Validation of Data:
            if "requestId" not in data or "employeeId" not in data:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Required Fields are Empty"
                }

            request_Id = data.get('requestId')
            transports = data.get('transports')
            employee_id = data.get('employeeId')

            # Validating the Request_ID already exist or not:
            query = "SELECT TOP 1 1 AS exists_flag FROM travelrequest WHERE request_id = ?"
            cursor.execute(query, request_Id)
            result = cursor.fetchone()

            if result is None:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Request ID Not Exists!!"
                }

            if transport_type == "flight":
                if transports is None:
                    return {
                        "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                        "responseMessage": "Required Fields are Empty"
                    }
                result = flight_data(cursor, connection, request_Id, transports, employee_id)
                return result
            elif transport_type == "train":
                if transports is None:
                    return {
                        "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                        "responseMessage": "Required Fields are Empty"
                    }
                result = train_data(cursor, connection, request_Id, transports, employee_id)
                return result
            elif transport_type == "bus":
                if transports is None:
                    return {
                        "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                        "responseMessage": "Required Fields are Empty"
                    }
                result = bus_data(cursor, connection, request_Id, transports, employee_id)
                return result
            elif transport_type == "taxi":

                result = taxi_data(cursor, connection, data)
                return result
            elif transport_type == "carRental":
                result = carrental_data(cursor, connection, data)
                return result
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)  # Error Code comes here
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

            # Code to Delete the previous Data related to that request ID:
            sql_query = "DELETE FROM hotel WHERE request_id = ?"
            cursor.execute(sql_query, (request_id,))
            connection.commit()

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

            for diem in diems:
                diem['requestId'] = request_id

            # Code to Delete the previous Data related to that request ID:
            sql_query = "DELETE FROM perdiem WHERE request_id = ?"
            cursor.execute(sql_query, (request_id,))
            connection.commit()

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
    # Validation for the Connection on DB/Server:
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


# 7. Other Expense API
@app.route('/other-expense', methods=['GET', 'POST'])
@jwt_required()
def other_expense():
    if not connection:
        custom_error_response = {
            "responseMessage": "Database Connection Error",
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "reason": "Failed to connect to the database. Please try again later."
        }
        # Return the custom error response with a 500 status code
        return jsonify(custom_error_response)

    if request.method == "GET":
        request_id = request.headers.get("requestId")
        query = "SELECT international_roaming, incident_expense from travelrequest where request_id=?"
        cursor.execute(query, (request_id,))

        # Fetch the data
        other_expense_data = cursor.fetchone()

        # Check if data is found
        if other_expense_data:
            international_roaming, incident_expense = other_expense_data
        else:
            international_roaming = None
            incident_expense = None

        response_data = {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Other Expense Data Fetched",
            "data": {
                "internationalRoaming": international_roaming,
                "incidentExpense": incident_expense
            }
        }
        return jsonify(response_data)
    if request.method == "POST":
        try:
            data = request.get_json()
            if "requestPolicy" not in data or "requestId" not in data:
                return jsonify({
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "(DEBUG) -> Request Policy and Request ID is required Field!!"
                })

            # Validation of the international expense and internation roaming as per the requestPolicy.

            request_id = data.get("requestId")
            if "incident_expense" in data or "international_roaming" in data:
                international_roaming = data.get("international_roaming")
                incident_expense = data.get("incident_expense")

                query = f"UPDATE travelrequest SET international_roaming=?, incident_expense=? WHERE request_id=?"
                cursor.execute(query, (international_roaming, incident_expense, request_id))
                connection.commit()
                return jsonify({
                    "responseCode": http_status_codes.HTTP_200_OK,
                    "responseMessage": "Other Expense Saved Successfully"
                })
        except Exception as err:
            return jsonify({
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong",
                "reason": str(err)
            })


# 8. Clearing Data API
@app.route('/clear-data', methods=['POST'])
@jwt_required()
def clear_data():
    try:
        data = request.get_json()
        request_id = data["requestId"]
        request_type = data["requestType"]
        if request_type == "transport":
            if "transportType" not in data:
                return {
                    "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                    "responseMessage": "Transport Type is a Required Field"
                }
        if "transportType" in data:
            transport_type = data["transportType"]
        else:
            transport_type = None

        # Validation of None Value
        if request_type is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "(DEBUG) -> requestType not found"
            }

        # Checking the Condition for the Request Type
        if request_type.lower() == "hotel":
            result = clear_hotel_data(cursor, connection, request_id)
            return result
        elif request_type.lower() == "perdiem":
            result = clear_perdiem_data(cursor, connection, request_id)
            return result
        elif request_type.lower() == "transport":
            result = clear_transport_data(cursor, connection, request_id, transport_type)
            return result
        else:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "(DEBUG) -> Invalid request_type Found"
            }
    except Exception as err:
        return {
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        }


# 9. Canceling Request Data API
@app.route('/cancel-request', methods=['POST'])
@jwt_required()
def cancel_request():
    try:
        data = request.get_json()
        request_id = data["requestId"]

        query = f"""
            Delete from travelrequest where travelrequest.request_id=?
        """

        cursor.execute(query, (request_id,))
        connection.commit()

        return {
            "responseMessage": "Request Cancelled Successfully",
            "responseCode": http_status_codes.HTTP_200_OK
        }
    except Exception as err:
        return {
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        }


# 10. Request Detail Page API
@app.route('/request-detail', methods=['GET'])
@jwt_required()
def request_detail():
    request_id = request.headers.get("requestId")
    query = """
        select 
            t.request_id,
            t.request_name,
            t.start_date,
            t.request_policy,
            e.employee_first_name,
            t.end_date,
            e.employee_id,
            t.status,
            t.cash_in_advance,
            h.estimated_cost hotel_estimated_cost,
            tmap.Flight_Cost,
            tbus.Bus_Cost,
            ttrain.Train_Cost,
            tcarrental.CarRental,
            taxicost.Taxi_Cost,
            COALESCE(t.cash_in_advance,0) + COALESCE(h.estimated_cost,0) + COALESCE(tmap.Flight_Cost,0) + COALESCE(tbus.Bus_Cost,0) + COALESCE(ttrain.Train_Cost,0)
            + COALESCE(tcarrental.CarRental,0) + COALESCE(taxicost.Taxi_Cost,0) as "Total Cost"
        FROM userproc05092023_1 e
        JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
        Join travelrequest t on t.user_id= e.employee_id
        Left Join ( select request_id,sum(estimated_cost) as estimated_cost from hotel group by request_id)
                h on h.request_id = t.request_id
        Left Join (select Distinct request_id from transport) trans on trans.request_id = t.request_id 
            and  trans.request_id = h.request_id
        Left Join ( select t.request_id,sum(tmap.estimated_cost) as "Flight_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
                    where t.transport_type = 'flight' group by t.request_id) 
                    tmap on tmap.request_id = t.request_id
        Left Join (select t.request_id, sum(tmap.estimated_cost) as "Bus_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
                    where t.transport_type = 'bus' group by t.request_id) tbus
                    on tbus.request_id = t.request_id
        Left Join (select t.request_id, sum(tmap.estimated_cost) as "Train_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
                    where t.transport_type = 'train' group by t.request_id) ttrain
                    on ttrain.request_id = t.request_id
        Left Join (select t.request_id, sum(tmap.estimated_cost) as "CarRental"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
                    where t.transport_type = 'carRental' group by t.request_id) tcarrental
                    on tcarrental.request_id = t.request_id
        Left Join (select t.request_id, sum(tmap.estimated_cost) as "Taxi_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
                    where t.transport_type = 'taxi' group by t.request_id) taxicost
                    on taxicost.request_id = t.request_id
        WHERE t.request_id = ?
    """

    result = cursor.execute(query, (request_id,)).fetchone()
    if not result:
        return {
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "RequestId is Invalid"
        }
    print("result: ", result)
    detail_data = [
        {
            "expenseType": "Cash In Advance",
            "amount": result[8]
        },
        {
            "expenseType": "Hotel Fare",
            "amount": result[9]
        },
        {
            "expenseType": "Air Fare",
            "amount": result[10]
        },
        {
            "expenseType": "Bus Fare",
            "amount": result[11]
        },
        {
            "expenseType": "Train Fare",
            "amount": result[12]
        },
        {
            "expenseType": "Car Rental",
            "amount": result[13]
        },
        {
            "expenseType": "Taxi Fare",
            "amount": result[14]
        },
    ]

    return {
        "requestId": result[0],
        "requestName": result[1],
        "startDate": result[2],
        "requestPolicy": result[3],
        "employeeFirstName": result[4],
        "endDate": result[5],
        "employeeId": result[6],
        "status": result[7],
        "totalCost": result[15],
        "data": detail_data,
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Request Detail "
    }


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

        # validation for status:
        if status != 'submitted':
            return {
                'responseCode': http_status_codes.HTTP_400_BAD_REQUEST,
                'responseMessage': 'Invalid Status Found'
            }

        # Validating request_id in travel Request Table:
        query = "SELECT TOP 1 user_id FROM travelrequest WHERE request_id = ?"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()

        if not result:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request ID Not Exists!!"
            }
        user_id = result[0]
        print("User Id: ", user_id)

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        # get the Manager's Email of the user_id
        email_query = """
            SELECT
                m.email_id AS manager_email,
                m.employee_id
            FROM
                userproc05092023_1 e
            JOIN
                userproc05092023_1 m ON e.manager_id = m.employee_id
            WHERE
                e.employee_id = ?
        """
        manager_data = cursor.execute(email_query, (user_id,)).fetchone()
        print("Manager Data: ", manager_data)
        if not manager_data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong!!!"
            }
        email_id, manager_id = manager_data
        print("Email_ID: ", email_id)
        print("Manager_ID: ", manager_id)

        employee_message = f"""
            Hi,
            
            Your Request Has been Submitted Successfully!!, You can withdraw it from "Pending Request" until it gets approved from your Manager.
            You can login to VYAY to review the request.
            
            Thanks,
            Team VYAY
        """
        manager_message = f"""
            Hi,
 
            There is one request from {user_id} for Approval!!, Please review and take a valid Action.
            You can login to VYAY to review the request using ..
             
            Thanks,
            Team VYAY
        """
        sender_email = "noreply@vyay.tech"
        msg = Message('Request for Approval!!', sender=sender_email, recipients=[email_id])
        msg.body = f"""
            Hi,
 
            There is one request from {user_id} for Approval!!, Please review and take a valid Action.
            You can login to VYAY to review the request using ..
             
            Thanks,
            Team VYAY
        """
        mail.send(msg)

        # Update the Notification in the Table Notification (Notification for Employee)
        query = "Insert into Notification (request_id, employee_id, created_at, current_status, message) Values (?,?,?,?,?)"
        current_date = date.today()

        # For Employee:
        cursor.execute(query, (request_id, user_id, current_date, 1, employee_message))
        connection.commit()

        # For Manager:
        cursor.execute(query, (request_id, manager_id, current_date, 1, manager_message))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
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
        comment = data.get("comment")

        # Validating request_id in travel Request Table:
        query = "SELECT cash_in_advance, user_id FROM travelrequest WHERE request_id = ? AND status = 'submitted'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()

        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Submitted to get Approve!!"
            }
        adv_cash, user_id = result

        # Validation of the Value getting in the status Variable:
        if status != "approved":
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Invalid Status Found !!"
            }

        query = f"UPDATE travelrequest SET status=?, comment_from_manager=? WHERE request_id=?"
        cursor.execute(query, (status, comment, request_id))
        connection.commit()

        # get the Manager's Email of the user_id
        email_query = """
            SELECT
                email_id,
                expense_administrator_email
            FROM
                userproc05092023_1
            WHERE
                employee_id=?
        """
        user_data = cursor.execute(email_query, (user_id,)).fetchone()

        if not user_data:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Something Went Wrong!!!"
            }
        email_id, exp_admin_email = user_data

        # Check is there Cash Advance in the Travel request (DONE)
        # Insert Query in the Table of the Notification:
        query = """INSERT INTO notification(
                        request_id,
                        employee_id,
                        created_at,
                        current_status
                   ) 
                   Values (?,?,?,?)
                """
        current_date = date.today()

        # Send Email to the User from Whom we got the request
        sender_email = "noreply@vyay.tech"
        msg = Message('Request Accepted Successfully', sender=sender_email, recipients=[email_id])
        msg.body = f"""
                        Hi,

                        Thanks for having Patience, Your Request has been Approved Successfully.
                        You can login to VYAY to review the request using ..

                        Thanks,
                        Team VYAY
                    """
        mail.send(msg)
        cursor.execute(query, (request_id, user_id, current_date, "approved"))
        connection.commit()

        # Checking for adv_cash and sending mail:
        if adv_cash != 0:
            # Send Email to the Respective Expense Admin who belongs to that User.
            sender_email = "noreply@vyay.tech"
            msg = Message('Request for send for Payment!!', sender=sender_email, recipients=[email_id])
            msg.body = f"""
                        Hi,
    
                        There is one request from {user_id} for Approval!!, Please review and take a valid Action.
                        You can login to VYAY to review the request using ..
    
                        Thanks,
                        Team VYAY
                    """
            mail.send(msg)
            cursor.execute(query, (request_id, user_id, current_date, "approved"))
            connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Request Approved Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


@app.route('/request-withdrawn', methods=['POST'])
@jwt_required()
def request_withdrawn():
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

        # Validating request_id in travel Request Table if approved then can be withdrawn:
        query = "SELECT 1 AS exists_flag FROM travelrequest WHERE request_id = ? AND status = 'approved'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()

        if result:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request Can't be Withdrawn!!"
            }

        # Validation of the Value getting in the status Variable:
        if status != 'initiated':
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Invalid Status Found"
            }

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Request Withdrawn Successfully"
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
        query = "SELECT user_id FROM travelrequest WHERE request_id = ? AND status = 'approved'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()

        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Approved by Manager"
            }

        # Validation of the Value getting in the status Variable:
        if status != "send for payment":
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Invalid Status Found"
            }

        query = f"UPDATE travelrequest SET status=? WHERE request_id=?"
        cursor.execute(query, (status, request_id))
        connection.commit()

        # Send Email to the User From Whom Request Sent.
        # Send Email to the Finance Person for this Request.
        # Update this record in the Notification Table:
        # Update in the Table of the Notification:
        # query = """INSERT INTO notification(
        #                 request_id,
        #                 employee_id,
        #                 created_at,
        #                 current_status
        #            )
        #            Values (?,?,?,?)
        #         """
        # current_date = date.today()
        # cursor.execute(query, (request_id, user_id, current_date, "approved"))
        # connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
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
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Request Payment Made Successfully"
        }

    except Exception as err:
        return jsonify({
            "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
            "responseMessage": "Something Went Wrong",
            "reason": str(err)
        })


@app.route('/request-send-back', methods=['POST'])
@jwt_required()
def request_send_back():
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
        comment = data.get("comment")

        # Validating request_id in travel Request Table:
        query = "SELECT 1 AS exists_flag FROM travelrequest WHERE request_id = ? AND status = 'submitted'"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()

        if result is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Request should be Submitted to Send Back!!"
            }

        # Validation of the Value getting in the status Variable:
        if status != "rejected":
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "Invalid Status Found"
            }

        query = f"UPDATE travelrequest SET status=?, comment_from_manager=? WHERE request_id=?"
        cursor.execute(query, (status, comment, request_id))
        connection.commit()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "responseMessage": "Request Sent Back Successfully"
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
        employeeId = request.headers.get('employeeId')

        # Condition of the Open Request:
        query = """
            Declare @employee_id varchar(100)
            set @employee_id=?
             
            select 'Open Request' as request_type,
            COALESCE(sum(case when travelrequest.status in ('initiated', 'rejected') then 1 else 0 end),0) as number_of_request 
            FROM userproc05092023_1 ee
            Join travelrequest on  travelrequest.user_id = ee.employee_id 
            where ee.employee_id = @employee_id
             
            UNION ALL
            --getting pending request
            select 'Pending Request' as request_type,
            COALESCE(sum(case when travelrequest.status in ('submitted') then 1 else 0 end),0) as number_of_request  
            FROM userproc05092023_1 ee
            Join travelrequest on  travelrequest.user_id = ee.employee_id 
            where ee.employee_id = @employee_id
             
             
            UNION ALL
            --getting manager to be approved request
            select 'To Be Approved Request' as request_type,
            COALESCE(sum(case when ee.user_type=1 and travelrequest.status in ('submitted') then 1 else 0 end),0) as number_of_request
            FROM userproc05092023_1 ee
            JOIN userproc05092023_1 m ON ee.manager_id = m.employee_id
            join travelrequest on travelrequest.user_id = ee.employee_id 
            where ee.employee_id = @employee_id OR ee.manager_id = @employee_id
             
            UNION ALL
            --Manager Total Request Data
            select 'Total Request' as request_type,
            COALESCE(sum(case 
                            when (ee.user_type=2 and travelrequest.status in ('rejected','submitted','approved')) OR
                            (ee.user_type=1 and travelrequest.status in ('rejected','submitted','approved')) Then 1
                            else 0
                            end),0) as number_of_request
            FROM userproc05092023_1 ee
            join travelrequest on travelrequest.user_id = ee.employee_id 
            where ( ee.user_type = 1 and ee.employee_id = @employee_id )  or  ( ee.user_type = 2 and (ee.employee_id = @employee_id or ee.manager_id = @employee_id
            or  ee.manager_id IN (SELECT employee_id FROM userproc05092023_1 WHERE manager_id = @employee_id)))
        """
        cursor.execute(query, (employeeId,))
        requests = cursor.fetchall()

        arr = []
        for counts in requests:
            arr.append(counts[1])

        # Code to check if data exists or not!
        if len(arr):
            data = {
                "openRequest": arr[0],
                "pendingRequest": arr[1],
                "toBeApprovedRequest": arr[2],
                "totalRequest": arr[3]
            }
        else:
            data = {}

        # Create a response dictionary
        response = {
            'responseCode': 200,
            'data': data
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

        # Condition of Required Data in Request
        if employeeId is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "(DEBUG) -> EmployeeId are required Fields!!"
            }

        # Code block for fetching the request data from the travelrequest Table
        query = """
                SELECT DISTINCT
                    t.request_id,
                    t.request_name,
                    t.start_date,
                    t.request_policy,
                    e.employee_first_name,
                    e.employee_id,
                    t.status,
                    t.cash_in_advance+SUM(h.estimated_cost) AS total_estimated_cost
                FROM userproc05092023_1 e
                JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
                JOIN travelrequest t ON t.user_id = e.employee_id
                JOIN hotel h ON h.request_id = t.request_id
                JOIN transport trans ON trans.request_id = t.request_id
                JOIN transporttripmapping transmap ON trans.id = transmap.transport
                WHERE e.employee_id = ? OR e.manager_id = ?
                GROUP BY
                    t.request_id,
                    t.request_name,
                    t.start_date,
                    t.request_policy,
                    e.employee_first_name,
                    e.employee_id,
                    t.status,
                    t.cash_in_advance;
            """

        result = cursor.execute(query, (employeeId, employeeId,)).fetchall()

        manager_down_lines = [
            {
                "request_id": req[0],
                "request_name": req[1],
                "start_date": req[2],
                "request_policy": req[3],
                "employee_name": req[4],
                "Emp_id": req[5],
                "status": req[6],
                "total_amount": req[7],
            }
            for req in result
        ]
        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "data": manager_down_lines,
            "responseMessage": "Data Fetched Successfully"
        }
    except Exception as err:
        return {
            "error": str(err),
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong"
        }


# To Be Approved Request Under a Manager:
@app.route('/request-to-approved', methods=['GET'])
@jwt_required()
def request_tobe_approved():
    try:
        employeeId = request.headers.get('employeeId')

        # Condition of Required Data in Request
        if employeeId is None:
            return {
                "responseCode": http_status_codes.HTTP_400_BAD_REQUEST,
                "responseMessage": "(DEBUG) -> EmployeeId are required Fields!!"
            }

        # Code block for fetching the request data from the travelrequest Table
        query = """
                select t.request_id,t.request_name,t.start_date,t.request_policy,e.employee_first_name,e.employee_id,t.status, e.manager_id,m.employee_first_name
                from userproc05092023_1 e
                join userproc05092023_1 m on e.manager_id=m.employee_id
                join travelrequest t on t.user_id=e.employee_id
                WHERE e.manager_id=?
            """

        result = cursor.execute(query, (employeeId,)).fetchall()

        manager_down_lines = [
            {
                "request_id": req[0],
                "request_name": req[1],
                "start_date": req[2],
                "request_policy": req[3],
                "employee_name": req[4],
                "Emp_id": req[5],
                "status": req[6]
            }
            for req in result
        ]
        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "data": manager_down_lines,
            "responseMessage": "Hey You ... Sab Chal Rha hai!!"
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
            query = "SELECT * FROM travelrequest WHERE status='submitted' and user_id=?"
            pending_travel_request_data = cursor.execute(query, (employeeId,)).fetchall()
            pending_travel_request_list = [
                {
                    "request_id": req.request_id,
                    "request_name": req.request_name,
                    "request_policy": req.request_policy,
                    "start_date": req.start_date
                }
                for req in pending_travel_request_data
            ]
            return {
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Pending Travel Request List",
                "data": pending_travel_request_list
            }
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
            # query = "SELECT * FROM travelrequest WHERE status IN ('initiated', 'rejected') and user_id=?"
            query = """
                    select t.request_id,t.request_name,t.start_date,t.request_policy,e.employee_first_name,e.employee_id,t.status, e.manager_id,m.employee_first_name 
                    from userproc05092023_1 e 
                    JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
                    JOIN travelrequest t ON t.user_id = e.employee_id
                    WHERE e.employee_id=? AND t.status IN ('initiated', 'rejected');
            """
            open_travel_request_data = cursor.execute(query, (employeeId,)).fetchall()
            open_travel_request_list = [
                {
                    "request_id": req[0],
                    "request_name": req[1],
                    "start_date": req[2],
                    "request_policy": req[3],
                    "employee_name": req[4],
                    "emp_id": req[5],
                    "status": req[6]
                }
                for req in open_travel_request_data
            ]
            return {
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Open Travel Request List",
                "data": open_travel_request_list
            }
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
        # task_list = [{"label": policy.request_policy_name,
        #               "perDiem": bool(policy.perdiem),
        #               "cashAdvance": bool(policy.cashadvance),
        #               "internationRoaming": bool(policy.international_roaming),
        #               "incidentCharges": bool(policy.incident_charges)
        #               } for policy in request_policy_data]

        task_list = [{
            "label": policy.request_policy_name,
            "perDiem": bool(policy.perdiem),
            "cashAdvance": bool(policy.cashadvance),
            "internationRoaming": bool(policy.international_roaming),
            "incidentCharges": bool(policy.incident_charges),
            "otherExpense": False if not policy.international_roaming and not policy.incident_charges else True
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

    if organization is None or employee is None:
        return {
            "responseCode": 400,
            "responseMessage": "(DEBUG) -> employeeId and Organization are required field"
        }

    # Validating the organizationId and employeeId
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


@app.route('/need-help', methods=['GET', 'POST'])
# @jwt_required()
def need_help():
    if request.method == 'GET':
        try:
            query = "select * from needhelp"
            need_help_data = cursor.execute(query).fetchall()
            task_list = [{'Question': ques.question, 'Answer': ques.answer} for ques in need_help_data]
            return {
                "data": task_list,
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Questions Fetched Successfully"
            }
        except Exception as err:
            return {
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong !!!",
                "reason": str(err)
            }
    elif request.method == 'POST':
        try:
            data = request.get_json()
            request_message = data.get('requestMessage')

            sender_email = "noreply@vyay.tech"
            employee_email = data.get('employeeEmail')
            it_desk_email = "mavrider007@gmail.com"

            # Email to IT Support:
            msg = Message('Tickets Raised ', sender=sender_email, recipients=[it_desk_email])
            msg.body = request_message
            mail.send(msg)

            # Email to Employee:
            msg = Message('Request Sent', sender=sender_email, recipients=[employee_email])
            msg.body = f"""
                Hi,
                
                Thank you for submitting your request.
                
                Your Request has been Submitted, Support Team will get back to you soon.
                Thanks,
                Vyay Team
            """
            mail.send(msg)

            return {
                "responseCode": http_status_codes.HTTP_200_OK,
                "responseMessage": "Request Submitted Successfully"
            }
        except Exception as err:
            return {
                "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
                "responseMessage": "Something Went Wrong !!!",
                "reason": str(err)
            }


@app.route('/get-bulletin', methods=['GET'])
@jwt_required()
def get_notes():
    try:
        organization_id = request.headers.get('organization')
        query = "select bulletin_note from organization Where company_id=?"
        bulletin_data = cursor.execute(query, (organization_id,)).fetchone()

        return {
            "responseCode": http_status_codes.HTTP_200_OK,
            "data": {
                "bulletinNote": bulletin_data[0]
            },
            "responseMessage": "Bulletin Note Fetched Successfully."
        }
    except Exception as err:
        return {
            "responseCode": http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            "responseMessage": "Something Went Wrong !!!",
            "reason": str(err)
        }


@app.route('/notification', methods=['GET'])
@jwt_required()
def notification():
    if request.method == 'GET':
        user_id = request.headers.get('userId')
        print(user_id)
        query = "SELECT * from notification WHERE employee_id=?"
        cursor.execute(query, (user_id, ))
        notification_data = cursor.fetchall()
        notification_list = [{'id': notify.id, 'request_id': notify.request_id, "employee_id": notify.employee_id,
                              "created_date": notify.created_at, "current_status": notify.current_status,
                              "message": notify.message} for notify in notification_data]
        return {
            'responseCode': http_status_codes.HTTP_200_OK,
            'responseMessage': 'Notification fetched Successfully',
            'data': notification_list
        }


if __name__ == '__main__':
    app.run(debug=True)
