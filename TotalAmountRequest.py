# def total_amount_request(cursor, request_id):
#     query = """
#         select
#             COALESCE(h.estimated_cost,0) + COALESCE(tmap.Flight_Cost,0) + COALESCE(tbus.Bus_Cost,0) + COALESCE(ttrain.Train_Cost,0)
#             + COALESCE(tcarrental.CarRental,0) + COALESCE(taxicost.Taxi_Cost,0) + COALESCE(t.cash_in_advance,0) as "Total Cost"
#         FROM userproc05092023_1 e
#         JOIN userproc05092023_1 m ON e.manager_id = m.employee_id
#         Join travelrequest t on t.user_id= e.employee_id
#         Left Join ( select request_id,sum(estimated_cost) as estimated_cost from hotel group by request_id)
#                 h on h.request_id = t.request_id
#         Left Join (select Distinct request_id from transport) trans on trans.request_id = t.request_id
#             and  trans.request_id = h.request_id
#         Left Join ( select t.request_id,sum(tmap.estimated_cost) as "Flight_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
#                     where t.transport_type = 'flight' group by t.request_id)
#                     tmap on tmap.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.estimated_cost) as "Bus_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
#                     where t.transport_type = 'bus' group by t.request_id) tbus
#                     on tbus.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.estimated_cost) as "Train_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
#                     where t.transport_type = 'train' group by t.request_id) ttrain
#                     on ttrain.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.estimated_cost) as "CarRental"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
#                     where t.transport_type = 'carRental' group by t.request_id) tcarrental
#                     on tcarrental.request_id = t.request_id
#         Left Join (select t.request_id, sum(tmap.estimated_cost) as "Taxi_Cost"  from transport t left join transporttripmapping tmap on t.id = tmap.transport
#                     where t.transport_type = 'taxi' group by t.request_id) taxicost
#                     on taxicost.request_id = t.request_id
#         WHERE t.request_id=?
#     """
#     cursor.execute(query, (request_id,))
#     data = cursor.fetchone()
#     return data
#
#
# def total_perdiem_or_expense_amount(cursor, request_id, request_policy):
#     # Fetching incident_expense and international_roaming Expense:
#     request_query = """
#         Select
#             incident_expense,
#             international_roaming,
#             start_date,
#             end_date,
#             U.employee_currency_code,
#             Org.incident_expense_valid_days
#         from travelrequest T
#         JOIN userproc05092023_1 U ON T.user_id=U.employee_id
#         JOIN organization Org on U.organization=Org.company_id
#         WHERE request_id=?
#     """
#     data = cursor.execute(request_query, (request_id,)).fetchone()
#     incident_expense, international_roaming, start_date, end_date, currency_code, incident_expense_valid_days = data
#     days_difference = (end_date - start_date).days
#
#     # Query to fetch the Rate from the Country Table:
#     # country_query = "SELECT exchange_rate FROM country WHERE currency_code=?"
#     # exchange_rate = cursor.execute(country_query, (currency_code,)).fetchone()
#     # exchange_rate = exchange_rate[0]
#
#     # Fetching Per Diem Data:
#     query = "SELECT * from perdiem WHERE request_id=?"
#     request_perdiem_data = cursor.execute(query, (request_id,)).fetchall()
#     diems = [
#         {
#             'date': diem.diem_date,  # 'date': diem.diem_date.strftime('%d/%m/%Y'),
#             "breakfast": diem.breakfast,
#             "lunch": diem.lunch,
#             "dinner": diem.dinner
#         }
#         for diem in request_perdiem_data
#     ]
#
#     # Request Policy Check amount and Policy:
#     query = "Select * from requestpolicy where request_policy_name=?"
#     data = cursor.execute(query, (request_policy,)).fetchone()
#     if not data:
#         return 0
#
#     breakfast_count = 0
#     lunch_count = 0
#     dinner_count = 0
#     for diem in diems:
#         if diem['breakfast'] == 1:
#             breakfast_count += 1
#         elif diem['lunch'] == 1:
#             lunch_count += 1
#         elif diem['dinner'] == 1:
#             dinner_count += 1
#
#     total = ((data[8] * breakfast_count * 83.15) +
#              (data[9] * lunch_count * 83.15) +
#              (data[9] * dinner_count * 83.15) +
#              (data[10] * international_roaming * 83.15)
#              )
#
#     if days_difference >= incident_expense_valid_days:
#         incident_expense_amount = ((data[11] * days_difference) * 83.15)
#         total = total+incident_expense_amount
#     return total
