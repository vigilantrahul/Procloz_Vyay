def request_list(cursor, employee_id):
    query = """
        Declare @employee_id varchar(100)
        set @employee_id =?
         
        -- Query for Open Request
         
        select 'Open Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id = @employee_id 
        and t.status in ('initiated', 'rejected')
         
         
        UNION ALL
        --Query for pending request type
        select 'Pending Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id = @employee_id 
        and t.status in ('submitted')
         
         
        Union All
        -- To Be Approved Query for Manager Expense Administrator and Finance Administrator
        (
        select 'To Be Approved' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.manager_id = @employee_id
        and t.status in ('submitted')
         
        Union All
         
        select 'To Be Approved' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.expense_administrator = @employee_id
        and t.status in ('approved')
         
        Union All
        select 'To Be Approved' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
        and t.status in ('send for payment') 
        )
         
        UNION ALL
         
        -----------The below query is for TOTAL REQUEST Granular Data
        -- Total Query for Employee, Manager, Expense Administrator and Finance
        (
        select 'Total Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id = @employee_id 
        and t.status in ('initiated', 'rejected','submitted','approved','send for payment','paid')
         
         
        UNION ALL
        select 'Total Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.manager_id = @employee_id
        and t.status in ('submitted')
         
        Union All
        select 'Total Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.expense_administrator = @employee_id
        and t.status in ('approved')
         
        Union All
        select 'Total Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
        and t.status in ('send for payment')
         
        Union All
         
        select 'Total Request' as Type_of_Request,
        t.request_id,
        t.request_name,
        t.start_date,
        t.request_policy,
        e.employee_first_name,
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
        WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
        and t.status in ('paid') 
        )
    """
    cursor.execute(query, (employee_id, ))
    all_request_list = cursor.fetchall()
    return all_request_list


def pull_request(cursor, employee_id):
    query = """
            select 
                t.request_id,
                COALESCE(h.estimated_cost,0) + COALESCE(tmap.Flight_Cost,0) + COALESCE(tbus.Bus_Cost,0) + COALESCE(ttrain.Train_Cost,0)
                + COALESCE(tcarrental.CarRental,0) + COALESCE(taxicost.Taxi_Cost,0) + COALESCE(t.cash_in_advance,0) as "Total Cost"
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

