import asyncio
import datetime
import time
from http import HTTPStatus

import aiohttp
from flask import render_template, Response, request
from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db, service_manager
from services.barcode_gen_service import generate_barcode
from services.payfabric_service import create_and_process_transaction
from services.soap_requests.printing_service import print_air_bill
from utilities import strip_specials, custom_response, get_user_data, generate_air_bill_html, \
    register_package_notification, option_visible

printing_service_ns = Namespace("printing_service", description="Printing service")


@printing_service_ns.route("/print_air_bill")
class PrintAirBill(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:
            payload = printing_service_ns.payload or {}
            notification_email_address = strip_specials(payload.get("notification_email_address", "")).strip()
            multiple = strip_specials(payload.get("multiple", "")).strip()
            airbills = payload.get("airbills", "")
            return_labels = payload.get("return_labels", "")
            notification_type = payload.get("notification_type", "")

            get_label_size_query = f"SELECT PrintToLabel FROM UserProfile WHERE UID='{user_data.get('user_id')}'"
            app_db.execute_query(cursor, get_label_size_query)
            try:
                get_label_size = cursor.fetchall()[0]
            except IndexError:
                get_label_size = {'PrintToLabel': "1"}

            if str(get_label_size.get('PrintToLabel')) == "0":
                label_size = "s8_5x11"
            elif str(get_label_size.get('PrintToLabel')) == "1":
                label_size = "s4x5"
            elif str(get_label_size.get('PrintToLabel')) == "2":
                label_size = "s4x6_5"

            if multiple == "false":
                if airbills:
                    air_bill_data_response = asyncio.run(
                        print_airbill(air_bill_data=airbills, payload=payload, user_data=user_data,
                                      label_size=label_size))

                    response = asyncio.run(render_air_bill_html(air_bill_data=air_bill_data_response,
                                                                label_size=get_label_size.get('PrintToLabel'),
                                                                user_data=user_data,
                                                                notification_type=notification_type,
                                                                notification_email_address=notification_email_address))
                    return response
                else:
                    air_bill_data_response = asyncio.run(
                        print_airbill(payload=payload, user_data=user_data, label_size=label_size,
                                      return_label=return_labels))

                    response = asyncio.run(render_air_bill_html(air_bill_data=air_bill_data_response,
                                                                label_size=get_label_size.get('PrintToLabel'),
                                                                user_data=user_data,
                                                                notification_type=notification_type,
                                                                notification_email_address=notification_email_address))
                    return response
            elif multiple == "true":

                air_bill_data_response = asyncio.run(
                    print_airbill(air_bill_data=airbills, payload=payload, user_data=user_data,
                                  label_size=label_size, return_label=return_labels))

                response = asyncio.run(render_air_bill_html(air_bill_data=air_bill_data_response,
                                                            label_size=get_label_size.get('PrintToLabel'),
                                                            user_data=user_data,
                                                            notification_type=notification_type,
                                                            notification_email_address=notification_email_address))

                return response
        except IndexError:
            return custom_response("error", "No Airbill", HTTPStatus.BAD_REQUEST)
        except Exception:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@printing_service_ns.route("/get_print_label_type")
class GetPrintLabelType(Resource):
    def get(self):
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            get_label_type_query = "SELECT TypeID, LabelType FROM PrintToLabelType"

            app_db.execute_query(cursor, get_label_type_query)

            get_label_type = cursor.fetchall()

            return custom_response("success", "Label Types", HTTPStatus.OK, data=get_label_type)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        finally:
            app_db.close_connection(conn)


@printing_service_ns.route("/print_air_bill_ship_as_guest")
class PrintAirBillShipAsGuest(Resource):
    def post(self):
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)
        try:
            payload = printing_service_ns.payload or {}
            account_number = 1000
            from_address_1 = strip_specials(payload.get("from_address_1", "")).strip()
            from_country = strip_specials(payload.get("from_country", "")).strip()
            notification_email_address = strip_specials(payload.get("notification_email_address", "")).strip()
            cc_first_name = payload.get('cc_first_name', None)
            cc_last_name = payload.get('cc_last_name', None)
            cc_number = payload.get("cc_number", None)
            cc_type = payload.get("cc_type", None)
            cc_exp_month = payload.get("cc_exp_month", None)
            cc_exp_year = payload.get("cc_exp_year", None)
            cc_phone = payload.get("cc_phone", None)
            cc_email = payload.get("cc_email", None)
            billing_zip = payload.get("billing_zip", None)
            notification_type = payload.get("notification_type", "")

            label_size = "s8_5x11"
            user_data = {'account_number': account_number}
            air_bill_data_response = asyncio.run(
                print_airbill(payload=payload, user_data=user_data, label_size=label_size))

            for data in air_bill_data_response:
                if data[1] == "success":
                    airbill_number = data[0].get('air_bill_no', '')
                    update_payment_type_query = f"UPDATE IPackage SET PaymentType='C' WHERE AirbillNo='{airbill_number}' "
                    app_db.execute_query(cursor, update_payment_type_query)
                    app_db.commit_connection(conn)

                    airbill_data_query = f"EXEC dbo.sp_GetAirbillInfo '{airbill_number}', '{airbill_number}', '' "
                    app_db.execute_query(cursor, airbill_data_query)
                    airbill_data = cursor.fetchall()[0]

                    json_dic = dict()
                    json_dic['Card'] = {}
                    json_dic['Card']['Billto'] = {}
                    json_dic['Card']['CardHolder'] = {}
                    json_dic["Document"] = dict()
                    json_dic["Document"]["UserDefined"] = []
                    json_dic['Amount'] = float(airbill_data.get('EstimatedTotalCharge', 0))
                    json_dic["Card"]['Customer'] = "01000"
                    json_dic["Card"]['CardName'] = cc_type
                    json_dic["Card"]['IsDefaultCard'] = "false"
                    json_dic["Card"]['Account'] = cc_number
                    json_dic["Card"]['ExpDate'] = f"{cc_exp_month}{cc_exp_year}"
                    json_dic["Card"]['Phone'] = cc_phone
                    json_dic["Card"]['Email'] = cc_email
                    json_dic["Card"]['Billto']['Country'] = from_country
                    json_dic["Card"]['Billto']['Line1'] = from_address_1
                    json_dic["Card"]['Billto']['Zip'] = billing_zip
                    json_dic["Card"]['CardHolder']['FirstName'] = cc_first_name
                    json_dic["Card"]['CardHolder']['LastName'] = cc_last_name
                    json_dic["Currency"] = 'USD'
                    json_dic["Customer"] = "01000"
                    json_dic["Type"] = "Sale"
                    json_dic["SetupId"] = "EVO"
                    json_dic["Document"]["UserDefined"].append({"Name": "AirBillNo", "Value": airbill_number})

                    transaction_details_json = create_and_process_transaction(json_dic)
                    if transaction_details_json["Status"] == "Approved":
                        airbill_data['PrintedDate'] = datetime.datetime.strftime(datetime.datetime.now(), '%m/%d/%Y')
                        generate_barcode(airbill_number)
                        time.sleep(1)
                        service_manager.aws_s3.s3.download_file('prd-lso-genbarcode-dl', f'{airbill_number}.svg',
                                                                f'static/{airbill_number}.svg')

                        html = render_template("stdlabel.html", data=airbill_data)
                        response = Response(html, mimetype='text/html; charset=UTF-8')
                        response.headers['Cache-Control'] = 'max-age=0'
                        response.headers['Accept-Ranges'] = 'none'
                        for n_type in notification_type:
                            if n_type == "delivery":
                                n_type = "Delivered"
                            elif n_type == "pickup":
                                n_type = "Shipped"
                            elif n_type == "exception":
                                n_type = "Exceptions"
                            register_package_notification(air_bill_number=data[0].get('air_bill_no', ''),
                                                          email=notification_email_address,
                                                          n_type=n_type)
                        return response
                    else:
                        return custom_response("error",
                                               f"{transaction_details_json['Status']} {transaction_details_json['Message']}",
                                               HTTPStatus.BAD_REQUEST)

                elif data[1] == "error":
                    return data[0], 400
                else:
                    return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except IndexError:
            return custom_response("error", "No Airbill", HTTPStatus.BAD_REQUEST)
        except Exception:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


async def print_airbill(air_bill_data=None, payload=None, user_data=None, label_size=None,
                        return_label=0):
    service_type = strip_specials(payload.get("service_type", "")).strip()
    from_name = strip_specials(payload.get("from_name", "")).strip()
    from_phone = strip_specials(payload.get("from_phone", "")).strip()
    from_company = strip_specials(payload.get("from_company", "")).strip()
    from_address_1 = strip_specials(payload.get("from_address_1", "")).strip()
    from_address_2 = strip_specials(payload.get("from_address_2", "")).strip()
    from_zip_code = strip_specials(payload.get("from_zip_code", "")).strip()
    from_city = strip_specials(payload.get("from_city", "")).strip()
    from_state = strip_specials(payload.get("from_state", "")).strip()
    from_country = strip_specials(payload.get("from_country", "")).strip()
    to_name = strip_specials(payload.get("to_name", "")).strip()
    to_phone = strip_specials(payload.get("to_phone", "")).strip()
    to_company = strip_specials(payload.get("to_company", "")).strip()
    to_address_1 = strip_specials(payload.get("to_address_1", "")).strip()
    to_address_2 = strip_specials(payload.get("to_address_2", "")).strip()
    to_zip_code = strip_specials(payload.get("to_zip_code", "")).strip()
    to_city = strip_specials(payload.get("to_city", "")).strip()
    to_state = strip_specials(payload.get("to_state", "")).strip()
    to_country = strip_specials(payload.get("to_country", "")).strip()
    residential_delivery = strip_specials(payload.get("residential_delivery", "")).strip()
    length = strip_specials(payload.get("length", "")).strip()
    width = strip_specials(payload.get("width", "")).strip()
    height = strip_specials(payload.get("height", "")).strip()
    weight = strip_specials(payload.get("weight", "")).strip()
    lso_supplies_used = strip_specials(payload.get("lso_supplies_used", "")).strip()
    declared_value = strip_specials(payload.get("declared_value", "")).strip()
    bill_ref = strip_specials(payload.get("bill_ref", "")).strip()
    bill_ref_2 = strip_specials(payload.get("bill_ref_2", "")).strip()
    bill_ref_3 = strip_specials(payload.get("bill_ref_3", "")).strip()
    bill_ref_4 = strip_specials(payload.get("bill_ref_4", "")).strip()
    po_number = strip_specials(payload.get("po_number", "")).strip()
    promo_code = strip_specials(payload.get("promo_code", "")).strip()
    ott = strip_specials(payload.get("ott", "")).strip()
    add_saturday_service = strip_specials(payload.get("add_saturday_service", "")).strip()
    encode_label = strip_specials(payload.get("encode_label", "")).strip()
    label_format = strip_specials(payload.get("label_format", "")).strip()
    high_res = strip_specials(payload.get("high_res", "")).strip()
    zpl_based_image = strip_specials(payload.get("zpl_based_image", "")).strip()
    use_simple = strip_specials(payload.get("use_simple", "")).strip()
    delivery_notification = strip_specials(payload.get("delivery_notification", "")).strip()
    notification_email_address = strip_specials(payload.get("notification_email_address", "")).strip()
    signature_requirement = strip_specials(payload.get("signature_requirement", "")).strip()
    signature_release = strip_specials(payload.get("signature_release", "")).strip()
    signature_release_name = strip_specials(payload.get("signature_release_name", "")).strip()
    third_party_billing = strip_specials(payload.get("3rd_party_billing", "")).strip()
    account_number = user_data.get('account_number', '')

    if third_party_billing:
        if option_visible("ThirdPartyBilling", third_party_billing, 0):
            account_number = third_party_billing

    async with aiohttp.ClientSession() as session:
        tasks = []
        if not air_bill_data:
            request_data = dict(account_number=account_number, service_type=service_type, from_name=from_name,
                                from_phone=from_phone, from_company=from_company, from_address_1=from_address_1,
                                from_address_2=from_address_2, from_zip_code=from_zip_code, from_city=from_city,
                                from_state=from_state, from_country=from_country, to_name=to_name, to_phone=to_phone,
                                to_company=to_company, to_address_1=to_address_1, to_address_2=to_address_2,
                                to_zip_code=to_zip_code, to_city=to_city, to_state=to_state, to_country=to_country,
                                residential_delivery=residential_delivery, length=length, width=width, height=height,
                                weight=weight, lso_supplies_used=lso_supplies_used, declared_value=declared_value,
                                bill_ref=bill_ref, bill_ref_2=bill_ref_2, bill_ref_3=bill_ref_3, bill_ref_4=bill_ref_4,
                                po_number=po_number, promo_code=promo_code, ott=ott,
                                add_saturday_service=add_saturday_service, encode_label=encode_label,
                                label_format=label_format, label_size=label_size, high_res=high_res,
                                zpl_based_image=zpl_based_image, use_simple=use_simple,
                                delivery_notification=delivery_notification,
                                notification_email_address=notification_email_address,
                                signature_requirement=signature_requirement, signature_release=signature_release,
                                signature_release_name=signature_release_name)
            task = asyncio.ensure_future(print_air_bill(session=session, request_data=request_data))
            tasks.append(task)
            if int(return_label):
                request_data = dict(account_number=account_number, service_type=service_type, from_name=to_name,
                                    from_phone=to_phone, from_company=to_company, from_address_1=to_address_1,
                                    from_address_2=to_address_2, from_zip_code=to_zip_code, from_city=to_city,
                                    from_state=to_state, from_country=to_country, to_name=from_name,
                                    to_phone=from_phone, to_company=from_company, to_address_1=from_address_1,
                                    to_address_2=from_address_2, to_zip_code=from_zip_code, to_city=from_city,
                                    to_state=from_state, to_country=from_country,
                                    residential_delivery=residential_delivery, length=length, width=width,
                                    height=height, weight=weight, lso_supplies_used=lso_supplies_used,
                                    declared_value=declared_value, bill_ref=bill_ref, bill_ref_2=bill_ref_2,
                                    bill_ref_3=bill_ref_3, bill_ref_4=bill_ref_4, po_number=po_number,
                                    promo_code=promo_code, ott=ott, add_saturday_service=add_saturday_service,
                                    encode_label=encode_label, label_format=label_format, label_size=label_size,
                                    high_res=high_res, zpl_based_image=zpl_based_image, use_simple=use_simple,
                                    delivery_notification=delivery_notification,
                                    notification_email_address=notification_email_address,
                                    signature_requirement=signature_requirement, signature_release=signature_release,
                                    signature_release_name=signature_release_name)
                task = asyncio.ensure_future(print_air_bill(session=session, request_data=request_data))
                tasks.append(task)
        elif air_bill_data:
            for data in air_bill_data:
                request_data = dict(account_number=account_number, service_type=service_type, from_name=from_name,
                                    from_phone=from_phone, from_company=from_company, from_address_1=from_address_1,
                                    from_address_2=from_address_2, from_zip_code=from_zip_code, from_city=from_city,
                                    from_state=from_state, from_country=from_country, to_name=data.get('to_name'),
                                    to_phone=data.get('to_phone'), to_company=data.get('to_company'),
                                    to_address_1=data.get('to_address_1'), to_address_2=data.get('to_address_2'),
                                    to_zip_code=data.get('to_zip_code'), to_city=data.get('to_city'),
                                    to_state=data.get('to_state'), to_country=data.get('to_country'),
                                    residential_delivery=data.get('residential_delivery'), length=data.get('length'),
                                    width=data.get('width'), height=data.get('height'), weight=data.get('weight'),
                                    lso_supplies_used=lso_supplies_used, declared_value=data.get('declared_value'),
                                    bill_ref=bill_ref, bill_ref_2=bill_ref_2, bill_ref_3=bill_ref_3,
                                    bill_ref_4=bill_ref_4, po_number=po_number, promo_code=promo_code, ott=ott,
                                    add_saturday_service=add_saturday_service, encode_label=encode_label,
                                    label_format=label_format, label_size=label_size, high_res=high_res,
                                    zpl_based_image=zpl_based_image, use_simple=use_simple,
                                    delivery_notification=delivery_notification,
                                    notification_email_address=notification_email_address,
                                    signature_requirement=signature_requirement, signature_release=signature_release,
                                    signature_release_name=signature_release_name)
                task = asyncio.ensure_future(print_air_bill(session=session, request_data=request_data))
                tasks.append(task)
            for number in range(int(return_label)):
                try:
                    request_data = dict(account_number=account_number, service_type=service_type,
                                        from_name=air_bill_data[number].get('to_name'),
                                        from_phone=air_bill_data[number].get('to_phone'),
                                        from_company=air_bill_data[number].get('to_company'),
                                        from_address_1=air_bill_data[number].get('to_address_1'),
                                        from_address_2=air_bill_data[number].get('to_address_2'),
                                        from_zip_code=air_bill_data[number].get('to_zip_code'),
                                        from_city=air_bill_data[number].get('to_city'),
                                        from_state=air_bill_data[number].get('to_state'),
                                        from_country=air_bill_data[number].get('to_country'), to_name=from_name,
                                        to_phone=from_phone, to_company=from_company, to_address_1=from_address_1,
                                        to_address_2=from_address_2, to_zip_code=from_zip_code, to_city=from_city,
                                        to_state=from_state, to_country=from_country,
                                        residential_delivery=air_bill_data[number].get('residential_delivery'),
                                        length=air_bill_data[number].get('length'),
                                        width=air_bill_data[number].get('width'),
                                        height=air_bill_data[number].get('height'),
                                        weight=air_bill_data[number].get('weight'), lso_supplies_used=lso_supplies_used,
                                        declared_value=air_bill_data[number].get('declared_value'), bill_ref=bill_ref,
                                        bill_ref_2=bill_ref_2, bill_ref_3=bill_ref_3, bill_ref_4=bill_ref_4,
                                        po_number=po_number, promo_code=promo_code, ott=ott,
                                        add_saturday_service=add_saturday_service, encode_label=encode_label,
                                        label_format=label_format, label_size=label_size, high_res=high_res,
                                        zpl_based_image=zpl_based_image, use_simple=use_simple,
                                        delivery_notification=delivery_notification,
                                        notification_email_address=notification_email_address,
                                        signature_requirement=signature_requirement,
                                        signature_release=signature_release,
                                        signature_release_name=signature_release_name)
                    task = asyncio.ensure_future(print_air_bill(session=session, request_data=request_data))
                    tasks.append(task)
                except IndexError:
                    pass

        return await asyncio.gather(*tasks, return_exceptions=True)


async def render_air_bill_html(air_bill_data, label_size, user_data, notification_type, notification_email_address):
    html_task_list = []
    notification_task_list = []
    for data in air_bill_data:
        try:
            if data[1] == "success":
                generate_barcode(data[0].get('air_bill_no', ''))
                html_task = asyncio.ensure_future(
                    generate_air_bill_html(label_size=label_size, soap_response=data[0],
                                           user_id=user_data.get('user_id', '')))
                html_task_list.append(html_task)
                for n_type in notification_type:
                    if n_type == "delivery":
                        n_type = "Delivered"
                    elif n_type == "pickup":
                        n_type = "Shipped"
                    elif n_type == "exception":
                        n_type = "Exceptions"
                    notification_task = asyncio.ensure_future(
                        register_package_notification(air_bill_number=data[0].get('air_bill_no', ''),
                                                      email=notification_email_address, n_type=n_type))
                    notification_task_list.append(notification_task)
            elif data[1] == "error":
                return data[0], 400
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except (TypeError, IndexError):
            pass
    await asyncio.gather(*notification_task_list, return_exceptions=True)
    return await asyncio.gather(*html_task_list, return_exceptions=True)
