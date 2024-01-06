# def expense_request_list(cursor, employee_id):
#     query = """
#         Declare @employee_id varchar(100)
#         set @employee_id ='PC04'
#         ----------------------------------------------------------------------------------------------------------------------
#         /* Query for Open Request */
#         ----------------------------------------------------------------------------------------------------------------------
#         select 'Open Request' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0)+COALESCE(tbus.Final_Bus_Cost,0)+COALESCE(ttrain.Final_Train_Cost,0)+COALESCE(tcarrental.Final_CarRental_Cost,0)+COALESCE(taxicost.Final_Taxi_Cost,0)-COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id = @employee_id
#         and t.status in ('initiated', 'rejected')
#         union
#         SELECT
#          'Open Request' AS Type_of_Request,
#          expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#          'Submit a receipt' AS request_name,
#         expense_cost.bill_date as bill_date,
#          NULL AS start_date,
#          NULL AS request_policy,
#          expense_cost.employee_first_name AS employee_first_name,
#          expense_cost.employee_id AS employee_id,
#         expense_cost.status AS status,
#          NULL AS cash_in_advance,
#          NULL AS Final_Flight_Cost,
#          NULL AS Final_Bus_Cost,
#          NULL AS Final_Train_Cost,
#          NULL AS Final_CarRental_Cost,
#          NULL AS Final_Taxi_Cost,
#          expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('initiated', 'rejected')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status
#         ) expense_cost
#         WHERE expense_cost.user_id = @employee_id
#         UNION ALL
#
#         ----------------------------------------------------------------------------------------------------------------------
#         /* Query for Pending Request */
#         ----------------------------------------------------------------------------------------------------------------------
#         select 'Pending Request' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id = @employee_id
#         and t.status in ('submitted')
#         union
#         SELECT
#              'Pending Request' AS Type_of_Request,
#              expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#              'Submit a receipt' AS request_name,
#              expense_cost.bill_date as bill_date,
#              NULL AS start_date,
#              NULL AS request_policy,
#              expense_cost.employee_first_name AS employee_first_name,
#              expense_cost.employee_id AS employee_id,
#              expense_cost.status AS status,
#              NULL AS cash_in_advance,
#              NULL AS Final_Flight_Cost,
#              NULL AS Final_Bus_Cost,
#              NULL AS Final_Train_Cost,
#              NULL AS Final_CarRental_Cost,
#              NULL AS Final_Taxi_Cost,
#              expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('submitted')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status
#         ) expense_cost
#         WHERE expense_cost.user_id = @employee_id
#         UNION ALL
#         ----------------------------------------------------------------------------------------------------------------------
#         /* Query for To be Approved */
#         ----------------------------------------------------------------------------------------------------------------------
#         select 'To Be Approved' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.manager_id = @employee_id
#         and t.status in ('submitted')
#         union
#         SELECT
#              'To Be Approved' AS Type_of_Request,
#              expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#              'Submit a receipt' AS request_name,
#             expense_cost.bill_date as bill_date,
#              NULL AS start_date,
#              NULL AS request_policy,
#              expense_cost.employee_first_name AS employee_first_name,
#              expense_cost.employee_id AS employee_id,
#             expense_cost.status AS status,
#              NULL AS cash_in_advance,
#              NULL AS Final_Flight_Cost,
#              NULL AS Final_Bus_Cost,
#              NULL AS Final_Train_Cost,
#              NULL AS Final_CarRental_Cost,
#              NULL AS Final_Taxi_Cost,
#              expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         e.manager_id, SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('submitted')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status, e.manager_id
#         ) expense_cost
#         WHERE expense_cost.user_id != @employee_id and expense_cost.manager_id = @employee_id
#         UNION ALL
#         select 'To Be Approved' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.expense_administrator = @employee_id
#         and t.status in ('approved')
#         union
#         SELECT
#              'To Be Approved' AS Type_of_Request,
#              expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#              'Submit a receipt' AS request_name,
#              expense_cost.bill_date as bill_date,
#              NULL AS start_date,
#              NULL AS request_policy,
#              expense_cost.employee_first_name AS employee_first_name,
#              expense_cost.employee_id AS employee_id,
#              expense_cost.status AS status,
#              NULL AS cash_in_advance,
#              NULL AS Final_Flight_Cost,
#              NULL AS Final_Bus_Cost,
#              NULL AS Final_Train_Cost,
#              NULL AS Final_CarRental_Cost,
#              NULL AS Final_Taxi_Cost,
#              expense_cost.[Total Cost]
#         FROM (
#          SELECT
#             er.claim_number,
#             er.user_id,
#             er.bill_date,
#             e.employee_first_name,
#             e.employee_id,
#             er.status,
#             e.manager_id,
#             e.expense_administrator,
#             SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('approved')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#          er.status, e.manager_id, e.expense_administrator) expense_cost
#          WHERE expense_cost.user_id != @employee_id and expense_cost.expense_administrator =
#          @employee_id
#          UNION ALL
#          select 'To Be Approved' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
#         and t.status in ('send for payment')
#         union
#         SELECT
#             'To Be Approved' AS Type_of_Request,
#             expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#             'Submit a receipt' AS request_name,
#             expense_cost.bill_date as bill_date,
#             NULL AS start_date,
#             NULL AS request_policy,
#             expense_cost.employee_first_name AS employee_first_name,
#             expense_cost.employee_id AS employee_id,
#             expense_cost.status AS status,
#             NULL AS cash_in_advance,
#             NULL AS Final_Flight_Cost,
#             NULL AS Final_Bus_Cost,
#             NULL AS Final_Train_Cost,
#             NULL AS Final_CarRental_Cost,
#             NULL AS Final_Taxi_Cost,
#             expense_cost.[Total Cost]
#         FROM (
#          SELECT
#             er.claim_number,
#             er.user_id,
#             er.bill_date,
#             e.employee_first_name,
#             e.employee_id,
#             er.status,
#             e.manager_id,
#             e.expense_administrator,
#             e.finance_contact_person,
#             SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('send for payment')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#          er.status, e.manager_id, e.expense_administrator,e.finance_contact_person) expense_cost
#          WHERE expense_cost.user_id!= @employee_id and expense_cost.finance_contact_person =
#          @employee_id
#         ----------------------------------------------------------------------------------------------------------------------
#         /* Query for Total Request */
#         ----------------------------------------------------------------------------------------------------------------------
#         select 'Total Request' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id = @employee_id
#         and t.status in ('initiated', 'rejected','submitted','approved','send for payment','paid')
#         union
#         SELECT
#              'Total Request' AS Type_of_Request,
#              expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#              'Submit a receipt' AS request_name,
#              expense_cost.bill_date as bill_date,
#              NULL AS start_date,
#              NULL AS request_policy,
#              expense_cost.employee_first_name AS employee_first_name,
#              expense_cost.employee_id AS employee_id,
#              expense_cost.status AS status,
#              NULL AS cash_in_advance,
#              NULL AS Final_Flight_Cost,
#              NULL AS Final_Bus_Cost,
#              NULL AS Final_Train_Cost,
#              NULL AS Final_CarRental_Cost,
#              NULL AS Final_Taxi_Cost,
#              expense_cost.[Total Cost]
#         FROM (
#          SELECT
#              er.claim_number,
#              er.user_id,
#              er.bill_date,
#              e.employee_first_name,
#              e.employee_id,er.status,
#              e.manager_id,
#              SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('initiated', 'rejected','submitted','approved','send for payment','paid')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#          er.status, e.manager_id
#         ) expense_cost
#         WHERE expense_cost.user_id = @employee_id
#         UNION ALL
#         select 'Total Request' as Type_of_Request,
#              t.request_id,
#              t.request_name,
#              NULL as bill_date,
#              t.start_date,
#              t.request_policy,
#              e.employee_first_name,
#              e.employee_id,
#              t.status,
#              t.cash_in_advance,
#              tmap.Final_Flight_Cost,
#              tbus.Final_Bus_Cost,
#              ttrain.Final_Train_Cost,
#              tcarrental.Final_CarRental_Cost,
#              taxicost.Final_Taxi_Cost,
#              COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#              COALESCE(ttrain.Final_Train_Cost,0)
#              + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#              COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.manager_id = @employee_id
#         and t.status in ('submitted')
#         union
#         SELECT
#              'Total Request' AS Type_of_Request,
#              expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#              'Submit a receipt' AS request_name,
#              expense_cost.bill_date as bill_date,
#              NULL AS start_date,
#              NULL AS request_policy,
#              expense_cost.employee_first_name AS employee_first_name,
#              expense_cost.employee_id AS employee_id,
#              expense_cost.status AS status,
#              NULL AS cash_in_advance,
#              NULL AS Final_Flight_Cost,
#              NULL AS Final_Bus_Cost,
#              NULL AS Final_Train_Cost,
#              NULL AS Final_CarRental_Cost,
#              NULL AS Final_Taxi_Cost,
#              expense_cost.[Total Cost]
#         FROM (
#          SELECT
#              er.claim_number,
#              er.user_id,
#              er.bill_date,
#              e.employee_first_name,
#              e.employee_id,
#              er.status,
#              e.manager_id,
#              e.expense_administrator,
#              SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('submitted')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status, e.manager_id, e.expense_administrator
#         ) expense_cost
#         WHERE expense_cost.user_id != @employee_id and expense_cost.manager_id = @employee_id
#         UNION ALL
#         select 'Total Request' as Type_of_Request,
#             t.request_id,
#             t.request_name,
#             NULL as bill_date,
#             t.start_date,
#             t.request_policy,
#             e.employee_first_name,
#             e.employee_id,
#             t.status,
#             t.cash_in_advance,
#             tmap.Final_Flight_Cost,
#             tbus.Final_Bus_Cost,
#             ttrain.Final_Train_Cost,
#             tcarrental.Final_CarRental_Cost,
#             taxicost.Final_Taxi_Cost,
#             COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#             COALESCE(ttrain.Final_Train_Cost,0)
#             + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#             COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.expense_administrator = @employee_id
#         and t.status in ('approved')
#         union
#         SELECT
#          'Total Request' AS Type_of_Request,
#          expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#          'Submit a receipt' AS request_name,
#         expense_cost.bill_date as bill_date,
#          NULL AS start_date,
#          NULL AS request_policy,
#          expense_cost.employee_first_name AS employee_first_name,
#          expense_cost.employee_id AS employee_id,
#         expense_cost.status AS status,
#          NULL AS cash_in_advance,
#          NULL AS Final_Flight_Cost,
#          NULL AS Final_Bus_Cost,
#          NULL AS Final_Train_Cost,
#          NULL AS Final_CarRental_Cost,
#          NULL AS Final_Taxi_Cost,
#          expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         e.manager_id, e.expense_administrator, e.finance_contact_person,
#         SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('approved')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status, e.manager_id, e.expense_administrator,e.finance_contact_person
#         ) expense_cost
#         WHERE expense_cost.user_id != @employee_id and expense_cost.expense_administrator =
#         @employee_id
#         UNION ALL
#         select 'Total Request' as Type_of_Request,
#         t.request_id,
#         t.request_name,
#         NULL as bill_date,
#         t.start_date,
#         t.request_policy,
#         e.employee_first_name,
#         e.employee_id,
#         t.status,
#         t.cash_in_advance,
#         tmap.Final_Flight_Cost,
#         tbus.Final_Bus_Cost,
#         ttrain.Final_Train_Cost,
#         tcarrental.Final_CarRental_Cost,
#         taxicost.Final_Taxi_Cost,
#         COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#         COALESCE(ttrain.Final_Train_Cost,0)
#         + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#         COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
#         and t.status in ('send for payment')
#         union
#         SELECT
#          'Total Request' AS Type_of_Request,
#          expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#          'Submit a receipt' AS request_name,
#         expense_cost.bill_date as bill_date,
#          NULL AS start_date,
#          NULL AS request_policy,
#          expense_cost.employee_first_name AS employee_first_name,
#          expense_cost.employee_id AS employee_id,
#         expense_cost.status AS status,
#          NULL AS cash_in_advance,
#          NULL AS Final_Flight_Cost,
#          NULL AS Final_Bus_Cost,
#          NULL AS Final_Train_Cost,
#          NULL AS Final_CarRental_Cost,
#          NULL AS Final_Taxi_Cost,
#          expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         e.manager_id, e.expense_administrator, e.finance_contact_person,
#         SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('send for payment')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status, e.manager_id, e.expense_administrator,e.finance_contact_person
#         ) expense_cost
#         WHERE expense_cost.user_id!= @employee_id and expense_cost.finance_contact_person =
#         @employee_id
#         UNION ALL
#         select 'Total Request' as Type_of_Request,
#         t.request_id,
#         t.request_name,
#         NULL as bill_date,
#         t.start_date,
#         t.request_policy,
#         e.employee_first_name,
#         e.employee_id,
#         t.status,
#         t.cash_in_advance,
#         tmap.Final_Flight_Cost,
#         tbus.Final_Bus_Cost,
#         ttrain.Final_Train_Cost,
#         tcarrental.Final_CarRental_Cost,
#         taxicost.Final_Taxi_Cost,
#         COALESCE(tmap.Final_Flight_Cost,0) + COALESCE(tbus.Final_Bus_Cost,0) +
#         COALESCE(ttrain.Final_Train_Cost,0)
#         + COALESCE(tcarrental.Final_CarRental_Cost,0) + COALESCE(taxicost.Final_Taxi_Cost,0) -
#         COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join expenserequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from expensehotel group by
#         request_id)
#         h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from expensetransport) trans on trans.request_id = t.request_id
#         and trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.final_amount) as "Final_Flight_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'flight' group by t.request_id)
#         tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Bus_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'bus' group by t.request_id) tbus
#         on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Train_Cost" from expensetransport
#         t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'train' group by t.request_id) ttrain
#         on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_CarRental_Cost" from
#         expensetransport t left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'carRental' group by t.request_id) tcarrental
#         on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.final_amount) as "Final_Taxi_Cost" from expensetransport t
#         left join expensetransporttripmapping tmap on t.id = tmap.transport
#         where t.transport_type = 'taxi' group by t.request_id) taxicost
#         on taxicost.request_id = t.request_id
#         WHERE e.employee_id != @employee_id and e.finance_contact_person = @employee_id
#         and t.status in ('paid')
#         union
#         SELECT
#          'Total Request' AS Type_of_Request,
#          expense_cost.claim_number AS request_id, -- Placeholder for request_id under claim_number
#          'Submit a receipt' AS request_name,
#         expense_cost.bill_date as bill_date,
#          NULL AS start_date,
#          NULL AS request_policy,
#          expense_cost.employee_first_name AS employee_first_name,
#          expense_cost.employee_id AS employee_id,
#         expense_cost.status AS status,
#          NULL AS cash_in_advance,
#          NULL AS Final_Flight_Cost,
#          NULL AS Final_Bus_Cost,
#          NULL AS Final_Train_Cost,
#          NULL AS Final_CarRental_Cost,
#          NULL AS Final_Taxi_Cost,
#          expense_cost.[Total Cost]
#         FROM (
#          SELECT er.claim_number, er.user_id, er.bill_date, e.employee_first_name,e.employee_id,er.status,
#         e.manager_id, e.expense_administrator, e.finance_contact_person,
#         SUM(er.final_amount) AS "Total Cost"
#          FROM expensesubmitreceipt er
#          LEFT JOIN userproc05092023_1 e ON er.user_id = e.employee_id
#          WHERE er.status IN ('paid')
#          GROUP BY er.claim_number, er.user_id, er.bill_date, e.employee_first_name, e.employee_id,
#         er.status, e.manager_id, e.expense_administrator,e.finance_contact_person
#         ) expense_cost
#         WHERE expense_cost.user_id!= @employee_id and expense_cost.finance_contact_person =
#         @employee_id
#     """
#
#     cursor.execute(query, (employee_id,))
#     all_expense_request_list = cursor.fetchall()
#     return all_expense_request_list
