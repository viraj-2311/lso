import csv
import io
from http import HTTPStatus
from io import TextIOWrapper

import xlsxwriter as xlsxwriter
from flask import request, send_file, make_response
from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db
from utilities import strip_specials, custom_response, get_user_data, validate_phone

addressbook_ns = Namespace("/addressbook", description="Addressbook related operations")


def quickcode_exists(quickcode, uid, cursor):
    """
    This function will check if quick code is already exists or not
    :param quickcode: quick code
    :param uid: user id
    :param cursor: database cursor
    :return: return the quick code data if exists
    """
    try:
        quickcode_exist_query = f"SELECT QuickCode FROM WebLocation WHERE QuickCode='{quickcode}' AND UID='{uid}'"
        app_db.execute_query(cursor, quickcode_exist_query)
        return cursor.fetchall()[0]
    except (_mssql.MssqlDatabaseException, IndexError):
        return None


def validate_file(filename):
    """
    This function will validate the file type
    :param filename: file name
    :return: return True if the file extension is csv
    """
    try:
        if filename.split(".")[-1] == "csv":
            return True
    except IndexError:
        return False


@addressbook_ns.route("/add_address")
class AddAddress(Resource):
    """
    This endpoint will add an address to the authenticated user's account
    """

    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = addressbook_ns.payload or {}
        ab_quickcode = strip_specials(payload.get('ab_quickcode', '')).strip()
        ab_name = strip_specials(payload.get('ab_name', '')).strip()
        ab_phone = strip_specials(payload.get('ab_phone', '')).strip()
        ab_company = strip_specials(payload.get('ab_company', '')).strip()
        ab_address_1 = strip_specials(payload.get('ab_address_1', '')).strip()
        ab_address_2 = strip_specials(payload.get('ab_address_2', '')).strip()
        ab_country = strip_specials(payload.get('ab_country', '')).strip()
        ab_zip_code = strip_specials(payload.get('ab_zip_code', '')).strip()
        ab_billing_ref = strip_specials(payload.get('ab_billing_ref', '')).strip()
        ab_residence = strip_specials(payload.get('ab_residence', '')).strip()
        ab_city = strip_specials(payload.get('ab_city', '')).strip()
        ab_state = strip_specials(payload.get('ab_state', '')).strip()

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:

            if not ab_quickcode:
                return custom_response("error", "Please enter a valid Quick Code.", HTTPStatus.BAD_REQUEST)

            if quickcode_exists(ab_quickcode, user_data.get('user_id', ''), cursor):
                return custom_response("error",
                                       f"Quick code {ab_quickcode} already exists. Enter a different QuickCode.",
                                       HTTPStatus.BAD_REQUEST)

            if not ab_name:
                return custom_response("error", "Please enter a valid Receiving Name.", HTTPStatus.BAD_REQUEST)
            elif not ab_phone:
                return custom_response("error", "Please enter a valid Receiving Phone Number.", HTTPStatus.BAD_REQUEST)
            elif not ab_company:
                return custom_response("error", "Please enter a valid Receiving Company Name.", HTTPStatus.BAD_REQUEST)
            elif not ab_address_1:
                return custom_response("error", "Please enter a valid Receiving Address.", HTTPStatus.BAD_REQUEST)
            elif not ab_zip_code:
                return custom_response("error", "Please enter a valid Receiving zip Code.", HTTPStatus.BAD_REQUEST)

            ab_phone = validate_phone(ab_phone)
            if not ab_phone:
                return custom_response("error", "Please enter a valid Receiving Phone Number.", HTTPStatus.BAD_REQUEST)

            get_address_count = f"SELECT COUNT(*) as TotalCount FROM dbo.WebLocation WHERE UID ='{user_data.get('user_id', '')}'"
            app_db.execute_query(cursor, get_address_count)
            initial_count = cursor.fetchall()[0]
            add_contact_query = f"EXEC sp_ImportQuickcode 0, '{user_data.get('user_id', '')}', '{ab_quickcode}', '{ab_name}', " \
                                f"'{ab_company}', '{ab_address_1}', '{ab_address_2}', '{ab_city}', '{ab_state}'," \
                                f" '{ab_zip_code}', '{ab_phone}', 0, null, '{ab_residence}', '{ab_billing_ref}'," \
                                f" '{ab_country}'"

            app_db.execute_query(cursor, add_contact_query)
            app_db.commit_connection(conn)

            app_db.execute_query(cursor, get_address_count)
            after_count = cursor.fetchall()[0]
            if initial_count == after_count:
                return custom_response("error", "Check the fields", HTTPStatus.BAD_REQUEST)
            return custom_response("success", "Contact added.", HTTPStatus.OK)

        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@addressbook_ns.route("/get_address")
class GetAddress(Resource):
    """
    This endpoint will get all the address of the authenticated user
    """

    @get_user_data
    @cognito_auth_required
    def get(self):
        user_data = request.data
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)
        try:
            get_address_query = f"SELECT * FROM WebLocation WHERE UID='{user_data.get('user_id', '')}'"
            app_db.execute_query(cursor, get_address_query)
            get_address = cursor.fetchall()
            if get_address:
                return custom_response("success", "Address list.", HTTPStatus.OK, data=get_address)
            else:
                return custom_response("success", "No Address", HTTPStatus.OK, data=dict())
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception) as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@addressbook_ns.route("/edit_address")
class EditAddress(Resource):
    """
    This endpoint will edit particular address of authenticated user
    """

    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = addressbook_ns.payload or {}
        ab_quickcode = strip_specials(payload.get('ab_quickcode', '')).strip()
        ab_name = strip_specials(payload.get('ab_name', '')).strip()
        ab_phone = strip_specials(payload.get('ab_phone', '')).strip()
        ab_company = strip_specials(payload.get('ab_company', '')).strip()
        ab_address_1 = strip_specials(payload.get('ab_address_1', '')).strip()
        ab_address_2 = strip_specials(payload.get('ab_address_2', '')).strip()
        ab_country = strip_specials(payload.get('ab_country', '')).strip()
        ab_zip_code = strip_specials(payload.get('ab_zip_code', '')).strip()
        ab_billing_ref = strip_specials(payload.get('ab_billing_ref', '')).strip()
        ab_residence = strip_specials(payload.get('ab_residence', '')).strip()
        ab_city = strip_specials(payload.get('ab_city', '')).strip()
        ab_state = strip_specials(payload.get('ab_state', '')).strip()

        user_data = request.data
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:

            if not ab_name:
                return custom_response("error", "Please enter a valid Receiving Name.", HTTPStatus.BAD_REQUEST)
            elif not ab_phone:
                return custom_response("error", "Please enter a valid Receiving Phone Number.", HTTPStatus.BAD_REQUEST)
            elif not ab_company:
                return custom_response("error", "Please enter a valid Receiving Company Name.", HTTPStatus.BAD_REQUEST)
            elif not ab_address_1:
                return custom_response("error", "Please enter a valid Receiving Address.", HTTPStatus.BAD_REQUEST)
            elif not ab_zip_code:
                return custom_response("error", "Please enter a valid Receiving zip Code.", HTTPStatus.BAD_REQUEST)

            edit_contact_query = f"Update WebLocation set Name='{ab_name}', Address1='{ab_address_1}', " \
                                 f"Address2='{ab_address_2}', City='{ab_city}', State='{ab_state}', " \
                                 f"Zip='{ab_zip_code}', Phone='{ab_phone}', CompanyName='{ab_company}', " \
                                 f"Residence='{ab_residence}', CountryCode='{ab_country}', " \
                                 f"BillingRef='{ab_billing_ref}' WHERE UID='{user_data.get('user_id', '')}' AND " \
                                 f"QuickCode='{ab_quickcode}'"
            app_db.execute_query(cursor, edit_contact_query)
            app_db.commit_connection(conn)
            return custom_response("success", "Contact edited.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@addressbook_ns.route("/delete_address")
class DeleteAddress(Resource):
    """
    This endpoint will delete particular address of the authenticated user
    """

    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = addressbook_ns.payload or {}
        ab_quickcode_list = payload.get('ab_quickcode_list', '')

        user_data = request.data
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            for ab_quickcode in ab_quickcode_list:
                delete_contact_query = f"EXEC deleteQuickCode {user_data.get('user_id', '')}, '{ab_quickcode}'"
                app_db.execute_query(cursor, delete_contact_query)
                app_db.commit_connection(conn)
            return custom_response("success", "Contact deleted.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@addressbook_ns.route("/import_address")
class ImportAddress(Resource):
    """
    This endpoint will take an csv file and add addresses to the authenticated user's account
    """

    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = request.files['file']
        filename = payload.filename

        user_data = request.data
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if not validate_file(filename):
                return custom_response("error", "File has an invalid format.", HTTPStatus.BAD_REQUEST)
            else:
                csv_file = TextIOWrapper(payload, encoding='utf-8')
                csv_reader = csv.reader(csv_file, delimiter=',')

                for index, row in enumerate(csv_reader):
                    if not index:
                        if row[0] == "QuickCode" and row[1] == "AttnName" and row[2] == "CompanyName" and row[
                            3] == "Address" and row[4] == "Bldg/Suite" and row[5] == "City" and row[6] == "State" and \
                                row[7] == "Zip" and row[8] == "Phone" and row[9] == "Residence" and row[
                            10] == "CountryCode" and \
                                row[11] == "BillingRef":
                            continue
                        else:
                            return custom_response("error", "Please check the file", HTTPStatus.BAD_REQUEST)
                    else:
                        if len(row) != 12:
                            custom_response("error", "Please check the file.", HTTPStatus.BAD_REQUEST)
                        else:
                            add_contact_query = f"EXEC sp_ImportQuickcode @errorCode=0, " \
                                                f"@UID='{user_data.get('user_id', '')}', " \
                                                f"@QuickCode='{strip_specials(row[0]).upper()}', " \
                                                f"@AttnName='{strip_specials(row[1]).upper()}', " \
                                                f"@CompanyName='{strip_specials(row[2]).upper()}', " \
                                                f"@Address1='{strip_specials(row[3]).upper()}', " \
                                                f"@Address2='{strip_specials(row[4]).upper()}', " \
                                                f"@City='{strip_specials(row[5]).upper()}', " \
                                                f"@State='{strip_specials(row[6]).upper()}', " \
                                                f"@Zip='{strip_specials(row[7]).upper()}', " \
                                                f"@Phone='{strip_specials(row[8]).upper()}', " \
                                                "@FromLoc=0, @LastAirbill=NULL, " \
                                                f"@Residence='{strip_specials(row[9]).upper()}', " \
                                                f"@CountryCode='{strip_specials(row[10]).upper()}', " \
                                                f"@BillingRef='{strip_specials(row[11]).upper()}'"
                            app_db.execute_query(cursor, add_contact_query)
                            app_db.commit_connection(conn)
                return custom_response("success", "Contacts added.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@addressbook_ns.route("/export_address")
class ExportAddress(Resource):
    """
    This endpoint will export addresses in two different formats, whatever user choose
    1: csv
    2: xlsx
    """

    @get_user_data
    @cognito_auth_required
    def get(self):
        args = request.args
        file_type = args.get('file_type', '')
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        user_id = user_data.get('user_id', '')
        try:
            get_quick_code_query = f"SELECT QuickCode, Name, CompanyName, Address1, Address2, City, State, Zip, " \
                                   f"Phone, Residence, Coalesce(CountryCode, 'US') as CountryCode, BillingRef " \
                                   f"FROM Weblocation WHERE UID='{user_id}' AND fromLoc=0 " \
                                   f"ORDER BY QuickCode"
            app_db.execute_query(cursor, get_quick_code_query)
            get_quick_code = cursor.fetchall()

            if get_quick_code:
                csv_file = f"{user_id}.csv"
                xls_file = f"{user_id}.xlsx"

                if file_type == 'xls':
                    output = io.BytesIO()
                    workbook = xlsxwriter.Workbook(output)
                    worksheet = workbook.add_worksheet(str(user_id))
                    col_headers = ["QuickCode", "Name", "CompanyName", "Address1", "Address2", "City", "State", "Zip",
                                   "Phone", "Residence", "CountryCode", "BillingRef"]

                    col = 0
                    for i in col_headers:
                        worksheet.write(0, col, str(i))
                        col += 1

                    for i, ab_data in enumerate(get_quick_code, 1):
                        for j, data in enumerate(ab_data.values()):
                            worksheet.write(i, j, data)
                    workbook.close()
                    output.seek(0)
                    return send_file(output, attachment_filename=xls_file, as_attachment=True)
                elif file_type == 'csv':
                    col_headers = ["QuickCode", "Name", "CompanyName", "Address1", "Address2", "City", "State", "Zip",
                                   "Phone", "Residence", "CountryCode", "BillingRef"]
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=col_headers)
                    writer.writeheader()
                    for data in get_quick_code:
                        writer.writerow(data)

                    csv_output = make_response(output.getvalue())
                    csv_output.headers["Content-Disposition"] = f"attachment; filename={csv_file}"
                    csv_output.headers["Content-type"] = "text/csv"
                    return csv_output
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
