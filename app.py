import sys
from datetime import timedelta
import pyodbc
from flask import Flask, request, jsonify
from constants import http_status_codes
from flask_jwt_extended import create_access_token, create_refresh_token

app = Flask(__name__)

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


# ------------------------------- Data Fetch API -------------------------------
@app.get('/get-org')
def get_org():
    qry = f"SELECT * FROM organization"
    cursor.execute(qry)
    organization_data = cursor.fetchall()
    task_list = [{'Company Name': org.company_name, 'Company Onboard Date': org.company_onboard_date, "Company Id": org.company_id, "Company Contact Name": org.company_contact_name} for org in organization_data]
    return jsonify(task_list)


# ------------------------------- Authentication API -------------------------------
@app.post('/login')
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

    # Return the tokens to the client
    response_data = {
        "response_code": http_status_codes.HTTP_200_OK,
        "response_message": "Success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": user_data.employee_name,
            "designation": user_data.employee_business_title
        }
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True)
