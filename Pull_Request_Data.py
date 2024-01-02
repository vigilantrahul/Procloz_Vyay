def pull_request_data_api(request_id, cursor, connection, employee_id):
    try:
        # Select API from Travel Header:
        header_query = "Select * from travelrequest where request_id=?"
        cursor.execute(header_query, (request_id,))
        header_data = cursor.fetchone()
        user_id = header_data.user_id
        request_id = header_data.request_id
        request_name = header_data.request_name
        request_policy = header_data.request_policy
        start_date = header_data.start_date
        end_date = header_data.end_date
        status = "initiated"
        purpose = header_data.purpose
        cost_center = header_data.cost_center
        cash_in_advance = header_data.cash_in_advance
        reason_cash_in_advance = header_data.reason_cash_in_advance
        incident_expense = header_data.incident_expense
        international_roaming = header_data.international_roaming

        # Insert API for Expense Header:
        expense_header_query = """
            Insert into expenserequest (request_id, user_id, request_name, request_policy, start_date, end_date, purpose, status, cost_center, cash_in_advance, reason_cash_in_advance, incident_expense, international_roaming)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        cursor.execute(expense_header_query, (
        request_id, user_id, request_name, request_policy, start_date, end_date, purpose, status, cost_center,
        cash_in_advance, reason_cash_in_advance, incident_expense, international_roaming))
        connection.commit()

        # Select API from PerDiem:
        perdiem_query = "SELECT * from perdiem WHERE request_id=?"
        perdiem_data = cursor.execute(perdiem_query, (request_id,)).fetchall()
        perdiem_data = [t[1:] for t in perdiem_data]

        # Insert API for Expense PerDiem:
        expense_perdiem_query = "Insert into expenseperdiem (request_id, breakfast, lunch, dinner, diem_date) VALUES (?,?,?,?,?)"
        cursor.executemany(expense_perdiem_query, perdiem_data)
        connection.commit()

        # Select API from Hotel:
        hotel_query = "SELECT * from hotel WHERE request_id=?"
        hotel_data = cursor.execute(hotel_query, (request_id,)).fetchall()
        hotel_data = [t[1:] for t in hotel_data]

        # Insert API for Expense Hotel:
        expense_perdiem_query = "Insert into expensehotel (request_id, city_name, start_date, end_date, estimated_cost) VALUES (?,?,?,?,?)"
        cursor.executemany(expense_perdiem_query, hotel_data)
        connection.commit()

        # Select API from Transport:
        transport_query = "Select * from transport Where request_id=?"
        transport_data = cursor.execute(transport_query, (request_id,)).fetchall()

        for data in transport_data:
            transport_id = data.id
            request_id = data.request_id
            transport_type = data.transport_type
            trip_type = data.trip_type

            # Query to Insert the Data in the Expense Transport Table:
            transport_query = "Insert into expensetransport (request_id, transport_type, trip_type) VALUES (?,?,?)"
            cursor.execute(transport_query, (request_id, transport_type, trip_type))
            connection.commit()

            # Get the ID of the inserted row
            transport_id_query = "select top 1 tprt.id from expensetransport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
            cursor.execute(transport_id_query, (request_id, employee_id,))
            row_id = cursor.fetchone()
            transport = row_id[0]
            transport_mapping_query = "Select * from transporttripmapping Where transport=?"
            transport_mapping_data = cursor.execute(transport_mapping_query, (transport_id,)).fetchall()

            for trip in transport_mapping_data:
                trip_from = trip.trip_from
                trip_to = trip.trip_to
                departure_date = trip.departure_date
                estimated_cost = trip.estimated_cost
                comment = trip.comment
                from_date = trip.from_date
                to_date = trip.to_date

                if transport_type == "flight" or transport_type == "bus" or transport_type == "train":
                    exp_transport_mapping_query = "Insert into expensetransporttripmapping (trip_from, trip_to, departure_date, estimated_cost, transport) VALUES (?,?,?,?,?)"
                    cursor.execute(exp_transport_mapping_query,
                                   (trip_from, trip_to, departure_date, estimated_cost, transport))
                    connection.commit()
                elif transport_type == "taxi":
                    expense_transport_mapping_query = "Insert into expensetransporttripmapping (transport, estimated_cost, comment) VALUES (?,?,?)"
                    cursor.execute(expense_transport_mapping_query, (transport, estimated_cost, comment))
                    connection.commit()
                elif transport_type == "carRental":
                    expense_transport_mapping_query = "Insert into expensetransporttripmapping (transport, estimated_cost, from_date, to_date, comment) VALUES (?,?,?,?,?)"
                    cursor.execute(expense_transport_mapping_query,
                                   (transport, estimated_cost, from_date, to_date, comment))
                    connection.commit()
        return {
            "responseCode": 200,
            "responseMessage": "Pull Request Setup Successfully"
        }
    except Exception as err:
        return{
            "reason": str(err),
            "responseCode": 500,
            "responseMessage": "Something Went Wrong"
        }
