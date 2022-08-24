import datetime
from http import HTTPStatus
import decimal

from flask import jsonify
from flask.globals import request
from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db
from utilities import strip_specials, custom_response, get_user_data

reports_service_ns = Namespace("reports_service", description="Reports Services")


@reports_service_ns.route("/get_reports")
class ReportsService(Resource):
    @get_user_data
    @cognito_auth_required
    def get(self):
        args = request.args
        now_date = datetime.datetime.now().strftime("%m/%d/%y")
        from_date = strip_specials(args.get("from_date", now_date)).strip()
        to_date = strip_specials(args.get("to_date", now_date)).strip()
        order_option = strip_specials(args.get("order_option", "")).strip()
        user_option = strip_specials(args.get("user_option", "")).strip()
        user_data = request.data
        user_id = user_data.get('user_id', '')
        cust_id = user_data.get('account_number', '')

        try:
            from_date = datetime.datetime.strptime(from_date, "%m/%d/%y")
            to_date = datetime.datetime.strptime(to_date, "%m/%d/%y")
        except ValueError:
            return custom_response("error", "Enter dates in mm/dd/yy format", HTTPStatus.BAD_REQUEST)

        from_month = f"0{from_date.month}" if len(str(from_date.month)) == 1 else str(from_date.month)
        from_day = f"0{from_date.day}" if len(str(from_date.day)) == 1 else str(from_date.day)
        from_year = f"{str(from_date.year)[-2:]}" if len(str(from_date.year)) == 4 else str(from_date.year)

        to_month = f"0{to_date.month}" if len(str(to_date.month)) == 1 else str(to_date.month)
        to_day = f"0{to_date.day}" if len(str(to_date.day)) == 1 else str(to_date.day)
        to_year = f"{str(to_date.year)[-2:]}" if len(str(to_date.year)) == 4 else str(to_date.year)

        beg_date = datetime.datetime.strptime(f"{from_month}/{from_day}/{from_year}", "%m/%d/%y")
        end_date = datetime.datetime.strptime(f"{to_month}/{to_day}/{to_year}", "%m/%d/%y")

        if beg_date < datetime.datetime.now() - datetime.timedelta(60):
            beg_date = datetime.datetime.now() - datetime.timedelta(60)

        end_date = end_date + datetime.timedelta(1)

        if order_option == "PrintedDate":
            date_option = order_option
            not_date_option = "PickupDate"
            order_by = f"{order_option}, BillingRef"

        elif order_option == "PickupDate":
            date_option = order_option
            not_date_option = "PrintedDate"
            order_by = f"{order_option}, BillingRef"

        elif order_option == "BillingRef":
            date_option = "PickupDate"
            not_date_option = "PrintedDate"
            order_by = f"{order_option}, PickupDate"

        else:
            date_option = "PickupDate"
            not_date_option = "PrintedDate"
            order_by = "PickupDate, BillingRef"

        if beg_date == "01/01/00":
            where_str = f"WHERE (({date_option} IS NULL) OR " \
                        f"(CONVERT(smalldatetime, convert(varchar(10), {date_option}, 120)) " \
                        f"BETWEEN CONVERT(smalldatetime, '{beg_date}') AND " \
                        f"CONVERT(smalldatetime, '{end_date}'))) "
        else:
            where_str = f"WHERE {date_option} >= '{beg_date}' AND {date_option} < '{end_date}'"

        if user_option != "" and user_option != "All_AND_3rdPartyShip":
            # only show packages with their account number
            where_str = f"{where_str} AND BillToCustID='{cust_id}' "

        if user_option == "UserShip" or user_option == "All_AND_3rdPartyShip":
            # only show packages shipped by this user id
            where_str = f"{where_str} AND User3 = '{user_id}' "

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            get_packages_query = f"SELECT {date_option}, {not_date_option}, ToCoName, DelivStatus, DelivDateTime, " \
                                 f"ToAttnName, ToAddress1, Toaddress2,  ToState, ToCity, ToZip, AirbillNo, " \
                                 f"DelivSignatureName, BillingRef, BillToCustID, ServiceType, TotalCharge + " \
                                 f"Coalesce(HandlingFee, 0) AS TotalCharge, OtherChargesOne AS Weight, " \
                                 f"EstimatedTotalCharge + Coalesce(HandlingFee, 0) AS EstimatedCost FROM IPackage " \
                                 f"{where_str} ORDER BY {order_by}, AirbillNo ASC"

            app_db.execute_query(cursor, get_packages_query)
            get_packages = cursor.fetchall()
            parsed_packages_response = parse_packages_response(get_packages)
            if not parsed_packages_response:
                return custom_response("success", "No reports", HTTPStatus.OK)
            else:
                from_date = datetime.datetime.strftime(from_date, "%m/%d/%y")
                to_date = datetime.datetime.strftime(to_date, "%m/%d/%y")
                url = f"/reports_service/get_reports?from_date={from_date}&to_date={to_date}&" \
                      f"order_option={order_option}&user_option={user_option}"
                return jsonify(
                    get_paginated_list(parsed_packages_response,
                                       url,
                                       start=int(args.get('start', 1)),
                                       limit=int(args.get('limit', 10))))
        except _mssql.MssqlDatabaseException as e:
            return custom_response("error", "Database error", HTTPStatus.BAD_GATEWAY)
        finally:
            app_db.close_connection(conn)


def get_paginated_list(data, url, start, limit):
    count = len(data)
    if count < start:
        return custom_response("error", "total count is less than start", HTTPStatus.BAD_REQUEST)

    obj = dict()
    obj['start'] = start
    obj['limit'] = limit
    obj['count'] = count

    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = f"{url}&start={start_copy}&limit={limit_copy}"

    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = f"{url}&start={start_copy}&limit={limit}"

    obj['data'] = data[(start - 1):(start - 1 + limit)]
    return obj


def get_package_detail(packages_response, package_key, fall_back=""):
    if isinstance(packages_response[package_key], decimal.Decimal):
        return str(packages_response[package_key])
    if packages_response[package_key] is None:
        return fall_back
    if isinstance(packages_response[package_key], datetime.datetime):
        return str(packages_response[package_key])
    return packages_response[package_key]


def parse_packages_response(data):
    package_response_list = []
    for packages_response in data:
        packages_response_dict = dict()
        packages_response_dict["printed_date"] = get_package_detail(packages_response, "PrintedDate")
        packages_response_dict["pickup_date"] = get_package_detail(packages_response, "PickupDate")
        packages_response_dict["to_co_name"] = get_package_detail(packages_response, "ToCoName")
        packages_response_dict["deliv_status"] = get_package_detail(packages_response, "DelivStatus")
        packages_response_dict["deliv_date_time"] = get_package_detail(packages_response, "DelivDateTime")
        packages_response_dict["to_attn_name"] = get_package_detail(packages_response, "ToAttnName")
        packages_response_dict["to_address_1"] = get_package_detail(packages_response, "ToAddress1")
        packages_response_dict["to_address_2"] = get_package_detail(packages_response, "Toaddress2")
        packages_response_dict["to_state"] = get_package_detail(packages_response, "ToState")
        packages_response_dict["to_city"] = get_package_detail(packages_response, "ToCity")
        packages_response_dict["to_zip"] = get_package_detail(packages_response, "ToZip")
        packages_response_dict["airbill_no"] = get_package_detail(packages_response, "AirbillNo")
        packages_response_dict["deliv_signature_name"] = get_package_detail(packages_response, "DelivSignatureName")
        packages_response_dict["billing_ref"] = get_package_detail(packages_response, "BillingRef")
        packages_response_dict["bill_to_cust_id"] = get_package_detail(packages_response, "BillToCustID")
        packages_response_dict["service_type"] = get_package_detail(packages_response, "ServiceType")
        packages_response_dict["total_charge"] = get_package_detail(packages_response, "TotalCharge")
        packages_response_dict["weight"] = get_package_detail(packages_response, "Weight")
        packages_response_dict["estimated_cost"] = get_package_detail(packages_response, "EstimatedCost")

        package_response_list.append(packages_response_dict)
    return package_response_list
