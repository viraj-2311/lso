from http import HTTPStatus

from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db
from utilities import strip_specials, mail_body, custom_response

order_supplies_ns = Namespace("order_supplies", description="Order Supplies")


@order_supplies_ns.route("/")
class OrderSupplies(Resource):
    @cognito_auth_required
    def post(self):
        payload = order_supplies_ns.payload or {}
        account_number = strip_specials(payload.get("account_number", "")).strip()
        service_type_on_air_bill = strip_specials(payload.get("service_type_on_air_bill", "")).strip()
        from_name = strip_specials(payload.get("from_name", "")).strip()
        from_area_code = strip_specials(payload.get("from_area_code", "")).strip()
        from_phone = strip_specials(payload.get("from_phone", "")).strip()
        from_company = strip_specials(payload.get("from_company", "")).strip()
        from_address_1 = strip_specials(payload.get("from_address_1", "")).strip()
        from_address_2 = strip_specials(payload.get("from_address_2", "")).strip()
        from_city = strip_specials(payload.get("from_city", "")).strip()
        from_zip = strip_specials(payload.get("from_zip", "")).strip()
        from_email = strip_specials(payload.get("from_email", "")).strip()
        billing_reference = strip_specials(payload.get("billing_reference", "")).strip()
        to_name = strip_specials(payload.get("to_name", "")).strip()
        to_area_code = strip_specials(payload.get("to_area_code", "")).strip()
        to_phone = strip_specials(payload.get("to_phone", "")).strip()
        to_company = strip_specials(payload.get("to_company", "")).strip()
        to_address_1 = strip_specials(payload.get("to_address_1", "")).strip()
        to_address_2 = strip_specials(payload.get("to_address_2", "")).strip()
        to_city = strip_specials(payload.get("to_city", "")).strip()
        to_zip = strip_specials(payload.get("to_zip", "")).strip()
        letter_pack_quantity = strip_specials(payload.get("letter_pack_quantity", "")).strip()
        tube_quantity = strip_specials(payload.get("tube_quantity", "")).strip()
        plastic_polypak_quantity = strip_specials(payload.get("plastic_polypak_quantity", "")).strip()
        small_cardboard_box_quantity = strip_specials(payload.get("small_cardboard_box_quantity", "")).strip()
        medium_cardboard_box_quantity = strip_specials(payload.get("medium_cardboard_box_quantity", "")).strip()
        large_cardboard_box_quantity = strip_specials(payload.get("large_cardboard_box_quantity", "")).strip()
        webship_air_bill_pouches_quantity = strip_specials(payload.get("webship_air_bill_pouches_quantity", "")).strip()
        pre_printed_air_bill_quantity = strip_specials(payload.get("pre_printed_air_bill_quantity", "")).strip()

        error_msg = "The following fields are required: "
        send_email = True

        if not from_address_1:
            error_msg += "FromAddress, "
            send_email = False
        if not from_name:
            error_msg += "FromName, "
            send_email = False
        if not from_company:
            error_msg += "FromCompany, "
            send_email = False
        if not from_city:
            error_msg += "FromCity, "
            send_email = False
        if not from_zip:
            error_msg += "FromZip, "
            send_email = False
        if not from_phone:
            error_msg += "FromPhone, "
            send_email = False
        if not account_number:
            error_msg += "Account Number, "
            send_email = False

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if not send_email:
                return {"status": "error", "response": error_msg}
            else:
                body = mail_body(account_number=account_number, from_email=from_email, from_name=from_name,
                                 from_company=from_company, from_phone=from_phone, from_address_1=from_address_1,
                                 from_address_2=from_address_2, from_city=from_city, from_zip=from_zip, to_name=to_name,
                                 to_company=to_company, to_phone=to_phone, to_address_1=to_address_1,
                                 to_address_2=to_address_2, to_city=to_city, to_zip=to_zip,
                                 billing_reference=billing_reference, letter_pack_quantity=letter_pack_quantity,
                                 tube_quantity=tube_quantity, plastic_polypak_quantity=plastic_polypak_quantity,
                                 webship_air_bill_pouches_quantity=webship_air_bill_pouches_quantity,
                                 pre_printed_air_bill_quantity=pre_printed_air_bill_quantity, green_abs_quantity="",
                                 large_cardboard_box_quantity=large_cardboard_box_quantity,
                                 medium_cardboard_box_quantity=medium_cardboard_box_quantity,
                                 small_cardboard_box_quantity=small_cardboard_box_quantity,
                                 service_type_on_air_bill=service_type_on_air_bill)
                subject = "Supply Order Form"

                recipient = "webmaster@LSO.com;leadqual@lso.com"

                send_email_query = f"EXEC sp_LSO_SendMail @EmailTo='{recipient}', @EmailSubject='{subject}', " \
                                   f"@EmailBody='{body}'"

                app_db.execute_query(cursor, send_email_query)
                app_db.commit_connection(conn)

                return {"status": "success", "message": "Done"}
        except _mssql.MssqlDatabaseException as e:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except Exception:
            return {"status": "error", "message": "Oops! An unexpected error occurred."}
        finally:
            app_db.close_connection(conn)
