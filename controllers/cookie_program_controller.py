from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource
from main import app_db, ops_db
import re
import pymssql

from utilities import custom_response

cookie_program_ns = Namespace("/cookieprogram", description="Customer Cookie Program")


@cookie_program_ns.route("/listcookies")
class ListCookies(Resource):

    def get(self):
        """
        List available cookie variants
        """
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)
        try:
            cookies_list_query = f"SELECT * FROM CookieType"
            app_db.execute_query(cursor, cookies_list_query)
            cookies_list = cursor.fetchall()
        finally:
            app_db.close_connection(conn)

        if cookies_list:
            return custom_response("Success", cookies_list, HTTPStatus.OK)
        else:
            return custom_response("Error", "N/A", HTTPStatus.INTERNAL_SERVER_ERROR)


def exec_ops_query(query):
    """

    :param query:
    :return: results of running provided query on the ops database
    """
    conn = ops_db.create_connection()
    cursor = ops_db.create_cursor(conn)
    try:
        ops_db.execute_query(cursor, query)
        result = cursor.fetchall()
    finally:
        ops_db.close_connection(conn)
    return result


@cookie_program_ns.route("/applycookie")
class CookieProgram(Resource):

    def get(self):
        """
        Send cookies to customers that have sent 12 priority packages in a month

        Input:
        @lsoaccountnumber: LSO Account number
        @billingzipcode: Billing Zip Code
        @airbillnumber: Any recent airbill number by the customer
        @shipmonth: Month and Year of shipment in YYYYMM

        @return: A list of values to autofill in the second page form or error if data is invalid
        """
        lsoaccountnumber = request.values.get('lsoaccountnumber', None)
        billingzipcode = request.values.get('billingzipcode', None)
        airbillnumber = request.values.get('airbillnumber', None)
        shipmonth = request.values.get('shipmonth', None)

        # Check if any of the inputs are empty

        if lsoaccountnumber is None:
            return custom_response("Error", "Please provide LSO Account number", HTTPStatus.BAD_REQUEST)

        if billingzipcode is None:
            return custom_response("Error", "Please provide Billing Zip Code", HTTPStatus.BAD_REQUEST)

        if airbillnumber is None:
            return custom_response("Error", "Please provide Airbill Number", HTTPStatus.BAD_REQUEST)

        if shipmonth is None:
            return custom_response("Error", "Please provide Shipment Month & Year", HTTPStatus.BAD_REQUEST)

        # Sanity checks

        if not lsoaccountnumber.isnumeric():
            return custom_response("Error", "LSO Account Number is not numeric", HTTPStatus.BAD_REQUEST)

        if not billingzipcode.isnumeric() or len(billingzipcode) < 5:
            return custom_response("Error", "Billing Zipcode is invalid", HTTPStatus.BAD_REQUEST)

        # Fetch customer details

        customer = exec_ops_query(
            f"SELECT CustID, CustName, AcctStatus, BillToZip, PhyAddress1, PhyAddress2, PhyCity, PhyState, PhyZip FROM [lonestar].[dbo].[Customer] WHERE CustID = {lsoaccountnumber}")

        if customer:
            customer = customer[0]
            if customer["BillToZip"].strip() != billingzipcode:
                return custom_response(
                    "Error",
                    "Your Billing Zipcode does not match your account",
                    HTTPStatus.BAD_REQUEST
                )
            elif customer["AcctStatus"] not in ["A", "R"]:
                return custom_response(
                    "Error",
                    "Your Account is not in good standing. Please Call and ask for someone in the billing department",
                    HTTPStatus.BAD_REQUEST
                )
        else:
            return custom_response("Error", "Customer ID Not found", HTTPStatus.BAD_REQUEST)

        # Fetch Airbills

        airbills = exec_ops_query(f"SELECT PickupDate FROM [lonestar].[dbo].[PkgHistory] WHERE BillToCustID = {lsoaccountnumber}")
        target_year = int(shipmonth[0:4])
        target_month = int(shipmonth[4:])
        airbills_in_target_month = [airbill['PickupDate'] for airbill in airbills if
                                    airbill['PickupDate'].month == target_month and airbill[
                                        'PickupDate'].year == target_year]

        if len(airbills_in_target_month) >= 12:
            return custom_response("Success", customer, HTTPStatus.OK)
        else:
            return custom_response("Error", "You have not shipped 12 airbills in the target month",
                                   HTTPStatus.BAD_REQUEST)

    def post(self):
        """
        Create a cookie order. City and State are auto populated by the DB based on zip code.

        Input:
        @lsoaccountnumber: LSO Account Number
        @yearmonth: Year and Month in YYYYMM format
        @toattnname: Attn Name
        @toconame: Company Name
        @toaddress1: Address 1
        @toaddress2: Address 2
        @billingzipcode: Zip code (City and State autopopulated using this)
        @email: E-Mail ID

        :return: Success or Error message
        """
        lsoaccountnumber = request.values.get('lsoaccountnumber', None)
        yearmonth = request.values.get('yearmonth', None)
        toattnname = request.values.get('toattnname', None)
        toconame = request.values.get('toconame', None)
        toaddress1 = request.values.get('toaddress1', None)
        toaddress2 = request.values.get('toaddress2', None)
        billingzipcode = request.values.get('billingzipcode', None)
        email = request.values.get('email', None)
        cookieid = request.values.get('cookieid', None)

        # Check if any of the inputs are empty

        if lsoaccountnumber is None:
            return custom_response("Error", "Please provide LSO Account number", HTTPStatus.BAD_REQUEST)

        if yearmonth is None:
            return custom_response("Error", "Please provide Shipment Month & Year", HTTPStatus.BAD_REQUEST)

        if toattnname is None:
            return custom_response("Error", "Please provide AttnName", HTTPStatus.BAD_REQUEST)

        if toconame is None:
            return custom_response("Error", "Please provide Company Name", HTTPStatus.BAD_REQUEST)

        if toaddress1 is None:
            return custom_response("Error", "Please provide Address Line 1", HTTPStatus.BAD_REQUEST)

        if toaddress2 is None:
            return custom_response("Error", "Please provide Address Line 2", HTTPStatus.BAD_REQUEST)

        if billingzipcode is None:
            return custom_response("Error", "Please provide Billing Zip Code", HTTPStatus.BAD_REQUEST)

        if email is None:
            return custom_response("Error", "Please provide E-Mail ID", HTTPStatus.BAD_REQUEST)

        if cookieid is None:
            return custom_response("Error", "Please provide the Cookie ID", HTTPStatus.BAD_REQUEST)

        # Sanity checks

        if not lsoaccountnumber.isnumeric():
            return custom_response("Error", "LSO Account Number is not numeric", HTTPStatus.BAD_REQUEST)

        if not yearmonth.isnumeric() or len(yearmonth) != 6:
            return custom_response("Error", "Please provide valid yearmonth in YYYYMM format", HTTPStatus.BAD_REQUEST)

        if not cookieid.isnumeric():
            return custom_response("Error", "Please provide valid numeric cookie ID", HTTPStatus.BAD_REQUEST)

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return custom_response("Error", "Please provide valid E-Mail ID", HTTPStatus.BAD_REQUEST)

        if not billingzipcode.isnumeric() or len(billingzipcode) < 5:
            return custom_response("Error", "Billing Zipcode is invalid", HTTPStatus.BAD_REQUEST)

        try:
            conn = app_db.create_connection()
            cursor = app_db.create_cursor(conn)
            output = cursor.callproc('spLogCookieOrder', (
                        pymssql.output(str),
                        pymssql.output(str),
                        lsoaccountnumber,
                        yearmonth,
                        toattnname,
                        toconame,
                        toaddress1,
                        toaddress2,
                        billingzipcode,
                        email,
                        cookieid,
                        '',
                        '',
            ))
        except pymssql._pymssql.DatabaseError:
            output = None
        finally:
            app_db.close_connection(conn)

        if output:
            if not output[0]:
                airbill_no = output[1]
                return custom_response("Success", airbill_no, HTTPStatus.OK)
            else:
                return custom_response("Error", f"Error: {output[0]}", HTTPStatus.BAD_REQUEST)
        else:
            return custom_response("Error", "Internal Server Error", HTTPStatus.INTERNAL_SERVER_ERROR)


