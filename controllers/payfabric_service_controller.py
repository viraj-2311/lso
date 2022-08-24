from http import HTTPStatus

from flask_restx import Namespace, Resource
from services.payfabric_service import create_and_process_transaction, create_credit_card
from utilities import strip_specials, custom_response

payfabric_service_ns = Namespace("payment", description="Process payment using PayFabric")


@payfabric_service_ns.route("/print")
class PayFabric(Resource):
    def post(self):
        payload = payfabric_service_ns.payload or {}
        amount = strip_specials(payload.get('amount', '')).strip()
        account = strip_specials(payload.get('cc_number', '')).strip()
        country = strip_specials(payload.get('country', '')).strip()
        line1 = strip_specials(payload.get('cc_billing_address', '')).strip()
        zip = strip_specials(payload.get('billing_zip', '')).strip()

        first_name = strip_specials(payload.get('cc_first_name', '')).strip()
        last_name = strip_specials(payload.get('cc_last_name', '')).strip()
        currency = strip_specials(payload.get('currency', 'USD')).strip()
        exp_month= strip_specials(payload.get('cc_exp_month', '')).strip()
        exp_year = strip_specials(payload.get('cc_exp_year', '')).strip()
        phone_number = strip_specials(payload.get('cc_phone_number', '')).strip()
        email = strip_specials(payload.get('cc_email', '')).strip()

        json_dic = {}
        json_dic['Card'] ={}
        json_dic['Card']['Billto'] ={}
        json_dic['Card']['CardHolder'] ={}


        json_dic['Amount'] = amount;
        json_dic["Card"]['Customer'] = "01000"
        json_dic["Card"]['IsDefaultCard'] = "false"
        json_dic["Card"]['Account'] = account
        json_dic["Card"]['ExpDate'] = f"{exp_month}{exp_year}"
        json_dic["Card"]['Phone'] = phone_number
        json_dic["Card"]['Email'] = email
        json_dic["Card"]['Billto']['Country'] = country
        json_dic["Card"]['Billto']['Line1'] = line1
        json_dic["Card"]['Billto']['Zip'] = zip
        json_dic["Card"]['CardHolder']['FirstName'] = first_name
        json_dic["Card"]['CardHolder']['LastName'] = last_name
        json_dic["Currency"] = currency
        json_dic["Customer"] = "01000"
        json_dic["Type"] = "Sale"
        json_dic["SetupId"] = "EVO"

        transaction_details_json = create_and_process_transaction(json_dic)
        return custom_response("Success", transaction_details_json, HTTPStatus.OK)


@payfabric_service_ns.route("/card")
class PayFabricCard(Resource):
    def post(self):
        payload = payfabric_service_ns.payload or {}
        account = strip_specials(payload.get('cc_number', '')).strip()
        line1 = strip_specials(payload.get('cc_billing_address', '')).strip()
        zip = strip_specials(payload.get('billing_zip', '')).strip()

        first_name = strip_specials(payload.get('cc_first_name', '')).strip()
        last_name = strip_specials(payload.get('cc_last_name', '')).strip()
        exp_month= strip_specials(payload.get('cc_exp_month', '')).strip()
        exp_year = strip_specials(payload.get('cc_exp_year', '')).strip()
        phone_number = strip_specials(payload.get('cc_phone_number', '')).strip()
        email = strip_specials(payload.get('cc_email', '')).strip()
        customer = strip_specials(payload.get('cc_customer', '01000')).strip()
        # resp = duplicate_account_creation_html_email(email)
        # respons = send_html_email("fanyuiharisu@gmail.com", first_name,line1,account, email)
        # return resp
        json_dic = {}
        json_dic['Billto'] = {}
        json_dic['CardHolder'] = {}
        json_dic['Account'] = account
        json_dic['Customer'] = customer
        json_dic['IsDefaultCard'] = 'false'
        json_dic['Tender'] = 'CreditCard'
        json_dic['ExpDate'] = f"{exp_month}{exp_year}"
        json_dic['Billto']['Line1'] = line1
        json_dic['Billto']['Phone'] = phone_number
        json_dic['Billto']['Zip'] = zip
        json_dic['Billto']['Email'] = email
        json_dic['CardHolder']['FirstName'] = first_name
        json_dic['CardHolder']['LastName'] = last_name

        card_response =  create_credit_card(json_dic)
        return custom_response("success", 'Card created', HTTPStatus.OK, data=card_response)
