from constants import http_status_codes, custom_status_codes


def clear_request_data(cursor, request_id, transport_type):
    # Condition is that request_id data available in the transport table regarding
    query = """DELETE FROM transport
               WHERE request_id = ? and transport_type=?;
            """
    cursor.execute(query, (request_id, transport_type, ))
    return {
        "responseMessage": "Data Cleared Successfully",
        "responseCode": http_status_codes.HTTP_200_OK
    }


def flight_data(cursor, connection, request_id, transports, employee_id):
    transport_type = transports['transportType']

    if 'trips' in transports and 'tripWay' in transports:
        trips = transports['trips']
        trip_type = transports['tripWay']
    else:
        # Handle the case when 'trips' and 'tripWay' keys are missing or have None values
        trips = None
        trip_type = None

    query = "SELECT TOP 1 1 AS exists_flag FROM transport WHERE request_id=? and transport_type=?"
    cursor.execute(query, (request_id, transport_type,))
    result = cursor.fetchone()

    # Condition is that request_id data available in the transport table
    if result:
        query = "DELETE FROM transport where request_id=?"
        cursor.execute(query, (request_id,))

    # Inserting the data in the transport table
    sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
    cursor.execute(sql_query, (request_id, transport_type, trip_type))
    connection.commit()

    # Get the ID of the inserted row
    transport_id_query = "select top 1 tprt.id from transport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
    cursor.execute(transport_id_query, (request_id, employee_id, ))
    row_id = cursor.fetchone()

    transport_id = row_id[0]

    # Condition for Trips
    if trips is not None:
        for trip in trips:
            trip['transport'] = transport_id

        # Construct the SQL query for bulk insert
        values = ', '.join([
            f"('{trip['from']}', '{trip['to']}', '{trip['departureDate']}', {trip['estimateCost']}, '{trip['transport']}')"
            for trip in trips
        ])
        query = f"INSERT INTO transporttripmapping (trip_from, trip_to, departure_date, estimated_cost, transport) VALUES {values}"
        cursor.execute(query)
        connection.commit()

    return ({
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Flight Data Saved Successfully"
    })


def train_data(cursor, connection, request_id, transports, employee_id):
    if 'trips' in transports and 'tripWay' in transports:
        trips = transports['trips']
        trip_type = transports['tripWay']
    else:
        # Handle the case when 'trips' and 'tripWay' keys are missing or have None values
        trips = None
        trip_type = None

    transport_type = transports['transportType']

    # Inserting the data in the transport table
    sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
    cursor.execute(sql_query, (request_id, transport_type, trip_type))
    connection.commit()

    # Get the ID of the inserted row
    transport_id_query = "select top 1 tprt.id from transport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
    cursor.execute(transport_id_query, (request_id, employee_id, ))
    row_id = cursor.fetchone()

    transport_id = row_id[0]

    # Condition for Trips
    if trips is not None:
        for trip in trips:
            trip['transport'] = transport_id

        # Construct the SQL query for bulk insert
        values = ', '.join([
            f"('{trip['from']}', '{trip['to']}', '{trip['departureDate']}', {trip['estimateCost']}, '{trip['transport']}')"
            for trip in trips
        ])
        query = f"INSERT INTO transporttripmapping (trip_from, trip_to, departure_date, estimated_cost, transport) VALUES {values}"
        cursor.execute(query)
        connection.commit()

    return ({
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Train Data Saved Successfully"
    })


def bus_data(cursor, connection, request_id, transports, employee_id):
    if 'trips' in transports and 'tripWay' in transports:
        trips = transports['trips']
        trip_type = transports['tripWay']
    else:
        # Handle the case when 'trips' and 'tripWay' keys are missing or have None values
        trips = None
        trip_type = None

    transport_type = transports['transportType']

    # Inserting the data in the transport table
    sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
    cursor.execute(sql_query, (request_id, transport_type, trip_type))
    connection.commit()

    # Get the ID of the inserted row
    transport_id_query = "select top 1 tprt.id from transport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
    cursor.execute(transport_id_query, (request_id, employee_id, ))
    row_id = cursor.fetchone()

    transport_id = row_id[0]

    # Condition for Trips
    if trips is not None:
        for trip in trips:
            trip['transport'] = transport_id

        # Construct the SQL query for bulk insert
        values = ', '.join([
            f"('{trip['from']}', '{trip['to']}', '{trip['departureDate']}', {trip['estimateCost']}, '{trip['transport']}')"
            for trip in trips
        ])
        query = f"INSERT INTO transporttripmapping (trip_from, trip_to, departure_date, estimated_cost, transport) VALUES {values}"
        cursor.execute(query)
        connection.commit()

    return ({
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Bus Data Saved Successfully"
    })


def taxi_data(cursor, connection, data):
    request_id = data["requestId"]
    transport_type = data["transportType"]
    employee_id = data["employeeId"]
    comment = data["comment"]
    estimate_cost = data["estimateCost"]
    trip_type = None

    # Inserting the data in the transport table
    sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
    cursor.execute(sql_query, (request_id, transport_type, trip_type))
    connection.commit()

    # Get the ID of the inserted row
    transport_id_query = "select top 1 tprt.id from transport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
    cursor.execute(transport_id_query, (request_id, employee_id, ))
    row_id = cursor.fetchone()
    transport_id = row_id[0]

    # Condition for Trips
    query = f"INSERT INTO transporttripmapping (comment, estimated_cost, transport) VALUES (?, ?, ?)"
    cursor.execute(query, (comment, estimate_cost, transport_id))
    connection.commit()

    return ({
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Taxi Data Saved Successfully"
    })


def carrental_data(cursor, connection, data):
    trip_type = None
    request_id = data["requestId"]
    transport_type = data["transportType"]
    employee_id = data["employeeId"]
    comment = data["comment"]
    from_date = data["startDate"]
    to_date = data["endDate"]
    estimate_cost = data["estimateCost"]

    # Inserting the data in the transport table
    sql_query = "INSERT INTO transport (request_id, transport_type, trip_type) VALUES (?, ?, ?)"
    cursor.execute(sql_query, (request_id, transport_type, trip_type))
    connection.commit()

    # Get the ID of the inserted row
    transport_id_query = "select top 1 tprt.id from transport as tprt INNER join travelrequest as trqst on tprt.request_id=trqst.request_id where tprt.request_id=? and trqst.user_id=? order by tprt.id DESC"
    cursor.execute(transport_id_query, (request_id, employee_id, ))
    row_id = cursor.fetchone()

    transport_id = row_id[0]

    query = f"INSERT INTO transporttripmapping (comment, estimated_cost, from_date, to_date, transport) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(query, (comment, estimate_cost, from_date, to_date, transport_id))
    connection.commit()

    return ({
        "responseCode": http_status_codes.HTTP_200_OK,
        "responseMessage": "Car Rental Data Saved Successfully"
    })
