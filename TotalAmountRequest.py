def total_amount_request(cursor, request_id):
    query = """
        select 
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
        WHERE t.request_id=?
    """
    cursor.execute(query, (request_id, ))
    data = cursor.fetchone()
    return data
