# from constants import http_status_codes, custom_status_codes
# from file_upload import upload_file
#
#
# def convert_to_float(value):
#     try:
#         return float(value)
#     except Exception as err:
#         print("Reason: ", err)
#         return 0
#
#
# def clear_expense_hotel_data(cursor, connection, request_id, request_type=None):
#     # Condition is that request_id data available in the transport table regarding
#     if request_type == "expense":
#         query = "DELETE FROM expensehotel WHERE request_id=?"
#     else:
#         query = "DELETE FROM hotel WHERE request_id=?"
#
#     cursor.execute(query, (request_id, ))
#     connection.commit()
#     return {
#         "responseMessage": "Data Cleared Successfully",
#         "responseCode": http_status_codes.HTTP_200_OK
#     }
#
#
# def clear_expense_perdiem_data(cursor, connection, request_id, request_type=None):
#     # Condition is that request_id data available in the transport table regarding
#     if request_type == "expense":
#         query = "DELETE FROM expenseperdiem WHERE request_id=?"
#     else:
#         query = "DELETE FROM perdiem WHERE request_id=?"
#
#     cursor.execute(query, (request_id, ))
#     connection.commit()
#     return {
#         "responseMessage": "Data Cleared Successfully",
#         "responseCode": http_status_codes.HTTP_200_OK
#     }
#
#
# def clear_expense_transport_data(cursor, connection, request_id, transport_type, request_type=None):
#     if request_type == "expense":
#         query = "DELETE FROM transport Where request_id=? and transport_type=?"
#     else:
#         query = "DELETE FROM transport Where request_id=? and transport_type=?"
#
#     cursor.execute(query, (request_id, transport_type, ))
#     connection.commit()
#     return {
#         "responseMessage": "Data Cleared Successfully",
#         "responseCode": http_status_codes.HTTP_200_OK
#     }
#
#
# def expense_flight_data(cursor, connection, request_id, transport_type, trip_way, objects, container_client, employee_id):
#     query = "SELECT TOP 1 1 AS exists_flag FROM expensetransport WHERE request_id=? and transport_type=?"
#     cursor.execute(query, (request_id, transport_type,))
#     result = cursor.fetchone()
#
#     # Condition is that request_id data available in the transport table
#     if result:
#         query = "DELETE FROM expensetransport where request_id=? and transport_type=?"
#         cursor.execute(query, (request_id, transport_type,))
#         connection.commit()
#
#     # Code for the request Process:
#     for obj in objects:
#         trip_from = obj.get('from')
#         trip_to = obj.get('to')
#         departureDate = obj.get('departureDate')
#         estimate_cost = obj.get('estimateCost', 0)
#         establishment_name = obj.get('establishmentName', None)
#         bill_date = obj.get('billDate', None)
#         bill_number = obj.get('billNumber', None)
#         bill_currency = obj.get('billCurrency', None)
#         bill_amount = obj.get('billAmount', 0)
#         exc_rate = obj.get('exchangeRate', 0)
#         final_amount = obj.get('finalAmount', 0)
#         expense_type = obj.get('expenseType', None)
#         file_name = obj.get('billFile', None)
#         original_file_name = obj.get('billFileOriginal', None)
#
#         estimate_cost = convert_to_float(estimate_cost)
#         bill_amount = convert_to_float(bill_amount)
#         final_amount = convert_to_float(final_amount)
#         exc_rate = convert_to_float(exc_rate)
#
#         # Checking for the File Exists or Not Exists:
#         if file_name is None and original_file_name is None:
#             file = obj.get('file')
#             file_data = upload_file(file, container_client)  # Uploading File Here
#             if "responseCode" in file_data and file_data["responseCode"] == 500:
#                 return file_data
#
#             file_name = file_data["filename"]
#             original_file_name = file_data["original_name"]
#
#         # Inserting the data in the transport table
#         sql_query = "INSERT INTO expensetransport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
#         cursor.execute(sql_query, (request_id, transport_type, trip_way))
#         connection.commit()
#
#         # Get the ID of the inserted row
#         transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
#         cursor.execute(transport_id_query, (request_id, employee_id, ))
#         row_id = cursor.fetchone()
#
#         transport_id = row_id[0]
#
#         query = f"INSERT INTO expensetransporttripmapping (trip_from, trip_to, departure_date, estimated_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exchange_rate, final_amount, expense_type, bill_file, bill_file_original_name, transport) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
#         cursor.execute(query, (trip_from, trip_to, departureDate, estimate_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exc_rate, final_amount, expense_type, file_name, original_file_name, transport_id))
#         connection.commit()
#         print("Data Inserted in Both Table")
#     return ({
#         "responseCode": http_status_codes.HTTP_200_OK,
#         "responseMessage": "Flight Data Saved Successfully"
#     })
#
#
# def expense_train_data(cursor, connection, request_id, transport_type, trip_way, objects, container_client, employee_id):
#     query = "SELECT TOP 1 1 AS exists_flag FROM expensetransport WHERE request_id=? and transport_type=?"
#     cursor.execute(query, (request_id, transport_type,))
#     result = cursor.fetchone()
#
#     # Condition is that request_id data available in the transport table
#     if result:
#         query = "DELETE FROM expensetransport where request_id=? and transport_type=?"
#         cursor.execute(query, (request_id, transport_type, ))
#         connection.commit()
#
#     # Code for the request Process:
#     for obj in objects:
#         trip_from = obj.get('from')
#         trip_to = obj.get('to')
#         departureDate = obj.get('departureDate')
#         estimate_cost = obj.get('estimateCost', 0)
#         bill_date = obj.get('billDate', None)
#         bill_number = obj.get('billNumber', None)
#         bill_currency = obj.get('billCurrency', None)
#         bill_amount = obj.get('billAmount', 0)
#         exc_rate = obj.get('exchangeRate', 0)
#         final_amount = obj.get('finalAmount', 0)
#         expense_type = obj.get('expenseType', None)
#         file_name = obj.get('billFile', None)
#         original_file_name = obj.get('billFileOriginal', None)
#
#         estimate_cost = convert_to_float(estimate_cost)
#         bill_amount = convert_to_float(bill_amount)
#         final_amount = convert_to_float(final_amount)
#         exc_rate = convert_to_float(exc_rate)
#
#         # Checking for the File Exists or Not Exists:
#         if file_name is None and original_file_name is None:
#             file = obj.get('file')
#             file_data = upload_file(file, container_client)  # Uploading File Here
#             if "responseCode" in file_data and file_data["responseCode"] == 500:
#                 return file_data
#
#             file_name = file_data["filename"]
#             original_file_name = file_data["original_name"]
#
#         # Inserting the data in the transport table
#         sql_query = "INSERT INTO expensetransport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
#         cursor.execute(sql_query, (request_id, transport_type, trip_way))
#         connection.commit()
#
#         # Get the ID of the inserted row
#         transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
#         cursor.execute(transport_id_query, (request_id, employee_id,))
#         row_id = cursor.fetchone()
#
#         transport_id = row_id[0]
#
#         query = f"INSERT INTO expensetransporttripmapping (trip_from, trip_to, departure_date, estimated_cost, bill_date, bill_number, bill_currency, bill_amount, exchange_rate, final_amount, expense_type, bill_file, bill_file_original_name, transport) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
#         cursor.execute(query, (trip_from, trip_to, departureDate, estimate_cost, bill_date, bill_number, bill_currency, bill_amount, exc_rate, final_amount, expense_type, file_name, original_file_name, transport_id))
#         connection.commit()
#
#     return ({
#         "responseCode": http_status_codes.HTTP_200_OK,
#         "responseMessage": "Train Data Saved Successfully"
#     })
#
#
# def expense_bus_data(cursor, connection, request_id, transport_type, trip_way, objects, container_client, employee_id):
#     query = "SELECT TOP 1 1 AS exists_flag FROM expensetransport WHERE request_id=? and transport_type=?"
#     cursor.execute(query, (request_id, transport_type,))
#     result = cursor.fetchone()
#
#     # Condition is that request_id data available in the transport table
#     if result:
#         query = "DELETE FROM expensetransport where request_id=? and transport_type=?"
#         cursor.execute(query, (request_id, transport_type, ))
#
#     # Code for the request Process:
#     for obj in objects:
#         trip_from = obj.get('from')
#         trip_to = obj.get('to')
#         departureDate = obj.get('departureDate')
#         estimate_cost = obj.get('estimateCost', 0)
#         bill_date = obj.get('billDate', None)
#         bill_number = obj.get('billNumber', None)
#         bill_currency = obj.get('billCurrency', None)
#         bill_amount = obj.get('billAmount', 0)
#         exc_rate = obj.get('exchangeRate', 0)
#         final_amount = obj.get('finalAmount', 0)
#         expense_type = obj.get('expenseType', None)
#         file_name = obj.get('billFile', None)
#         original_file_name = obj.get('billFileOriginal', None)
#
#         estimate_cost = convert_to_float(estimate_cost)
#         bill_amount = convert_to_float(bill_amount)
#         final_amount = convert_to_float(final_amount)
#         exc_rate = convert_to_float(exc_rate)
#
#         # Checking for the File Exists or Not Exists:
#         if file_name is None and original_file_name is None:
#             file = obj.get('file')
#             file_data = upload_file(file, container_client)  # Uploading File Here
#             if "responseCode" in file_data and file_data["responseCode"] == 500:
#                 return file_data
#
#             file_name = file_data["filename"]
#             original_file_name = file_data["original_name"]
#
#         # Inserting the data in the transport table
#         sql_query = "INSERT INTO expensetransport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
#         cursor.execute(sql_query, (request_id, transport_type, trip_way))
#         connection.commit()
#
#         # Get the ID of the inserted row
#         transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
#         cursor.execute(transport_id_query, (request_id, employee_id,))
#         row_id = cursor.fetchone()
#         transport_id = row_id[0]
#
#         query = f"INSERT INTO expensetransporttripmapping (trip_from, trip_to, departure_date, estimated_cost, bill_date, bill_number, bill_currency, bill_amount, exchange_rate, final_amount, expense_type, bill_file, bill_file_original_name, transport) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
#         cursor.execute(query, (trip_from, trip_to, departureDate, estimate_cost, bill_date, bill_number, bill_currency, bill_amount, exc_rate, final_amount, expense_type, file_name, original_file_name, transport_id))
#         connection.commit()
#
#     return ({
#         "responseCode": http_status_codes.HTTP_200_OK,
#         "responseMessage": "Bus Data Saved Successfully"
#     })
#
#
# def expense_taxi_data(cursor, connection, request_id, transport_type, trip_way, objects, container_client, employee_id):
#     query = "SELECT TOP 1 1 AS exists_flag FROM expensetransport WHERE request_id=? and transport_type=?"
#     cursor.execute(query, (request_id, transport_type,))
#     result = cursor.fetchone()
#
#     # Condition is that request_id data available in the transport table
#     if result:
#         query = "DELETE FROM expensetransport where request_id=? and transport_type=?"
#         cursor.execute(query, (request_id, transport_type,))
#
#     # Code for the request Process:
#     for obj in objects:
#         trip_from = obj.get('from')
#         trip_to = obj.get('to')
#         departureDate = obj.get('departureDate')
#         estimate_cost = obj.get('estimatedCost', 0)
#         establishment_name = obj.get('establishmentName', None)
#         bill_date = obj.get('billDate', None)
#         bill_number = obj.get('billNumber', None)
#         bill_currency = obj.get('billCurrency', None)
#         bill_amount = obj.get('billAmount', 0)
#         exc_rate = obj.get('exchangeRate', 0)
#         final_amount = obj.get('finalAmount', 0)
#         expense_type = obj.get('expenseType', None)
#         file_name = obj.get('billFile', None)
#         original_file_name = obj.get('billFileOriginal', None)
#
#         estimate_cost = convert_to_float(estimate_cost)
#         bill_amount = convert_to_float(bill_amount)
#         final_amount = convert_to_float(final_amount)
#         exc_rate = convert_to_float(exc_rate)
#
#         # Checking for the File Exists or Not Exists:
#         if file_name is None and original_file_name is None:
#             file = obj.get('file')
#             file_data = upload_file(file, container_client)  # Uploading File Here
#             if "responseCode" in file_data and file_data["responseCode"] == 500:
#                 return file_data
#
#             file_name = file_data["filename"]
#             original_file_name = file_data["original_name"]
#
#         # Inserting the data in the transport table
#         sql_query = "INSERT INTO expensetransport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
#         cursor.execute(sql_query, (request_id, transport_type, trip_way))
#         connection.commit()
#
#         # Get the ID of the inserted row
#         transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
#         cursor.execute(transport_id_query, (request_id, employee_id,))
#         row_id = cursor.fetchone()
#
#         transport_id = row_id[0]
#
#         query = f"INSERT INTO expensetransporttripmapping (trip_from, trip_to, departure_date, estimated_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exchange_rate, final_amount, expense_type, bill_file, bill_file_original_name, transport) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
#         cursor.execute(query, (trip_from, trip_to, departureDate, estimate_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exc_rate, final_amount, expense_type, file_name, original_file_name, transport_id))
#         connection.commit()
#
#     return ({
#         "responseCode": http_status_codes.HTTP_200_OK,
#         "responseMessage": "Taxi Data Saved Successfully"
#     })
#
#
# def expense_carrental_data(cursor, connection, request_id, transport_type, trip_way, request, container_client, employee_id):
#     query = "SELECT TOP 1 1 AS exists_flag FROM expensetransport WHERE request_id=? and transport_type=?"
#     cursor.execute(query, (request_id, transport_type,))
#     result = cursor.fetchone()
#
#     # Condition is that request_id data available in the transport table
#     if result:
#         query = "DELETE FROM expensetransport where request_id=? and transport_type=?"
#         cursor.execute(query, (request_id, transport_type,))
#
#     # Code for the request Process:
#     from_date = request.form.get('startDate', None)
#     to_date = request.form.get('endDate', None)
#     estimate_cost = request.form.get('estimatedCost', 0)
#     establishment_name = request.form.get('establishmentName', None)
#     bill_date = request.form.get('billDate', None)
#     bill_number = request.form.get('billNumber', None)
#     bill_currency = request.form.get('billCurrency', None)
#     bill_amount = request.form.get('billAmount', 0)
#     expense_type = request.form.get('expenseType', None)
#     exc_rate = request.form.get('exchangeRate', 0)
#     final_amount = request.form.get('finalAmount', 0)
#     file_name = request.form.get('billFile', None)
#     original_file_name = request.form.get('billFileOriginal', None)
#
#     estimate_cost = convert_to_float(estimate_cost)
#     bill_amount = convert_to_float(bill_amount)
#     final_amount = convert_to_float(final_amount)
#     exc_rate = convert_to_float(exc_rate)
#
#     # Checking for the File Exists or Not Exists:
#     if file_name is None and original_file_name is None:
#         file = request.files.get('file')
#         file_data = upload_file(file, container_client)  # Uploading File Here
#         if "responseCode" in file_data and file_data["responseCode"] == 500:
#             return file_data
#
#         file_name = file_data["filename"]
#         original_file_name = file_data["original_name"]
#
#     # Inserting the data in the transport table
#     sql_query = "INSERT INTO expensetransport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
#     cursor.execute(sql_query, (request_id, transport_type, trip_way))
#     connection.commit()
#
#     # Get the ID of the inserted row
#     transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
#     cursor.execute(transport_id_query, (request_id, employee_id,))
#     row_id = cursor.fetchone()
#
#     transport_id = row_id[0]
#
#     query = f"INSERT INTO expensetransporttripmapping (from_date, to_date, estimated_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exchange_rate, final_amount, expense_type, bill_file, bill_file_original_name, transport) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
#     cursor.execute(query, (from_date, to_date, estimate_cost, establishment_name, bill_date, bill_number, bill_currency, bill_amount, exc_rate, final_amount, expense_type, file_name, original_file_name, transport_id))
#     connection.commit()
#
#     return ({
#         "responseCode": http_status_codes.HTTP_200_OK,
#         "responseMessage": "Car Rental Data Saved Successfully"
#     })
