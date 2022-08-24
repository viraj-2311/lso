from xml.sax.saxutils import escape

import bs4

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8"
}


async def print_air_bill(session, request_data):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/PrintingService.asmx"
    data_url = "https://services.lso.com/PrintingService/v1_6"
    headers["SoapAction"] = f"{data_url}/PrintAirbill"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("PrintAirbill")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("Customer")}
                        {soap.soap_helper("AccountNumber", request_data.get('account_number'))}
                    {soap.soap("Customer", "close")}
                    {soap.soap_helper("ServiceType", escape(request_data.get('service_type')))}
                    {soap.soap_helper("FromName", escape(request_data.get('from_name')))}
                    {soap.soap_helper("FromPhone", request_data.get('from_phone'))}
                    {soap.soap_helper("FromCompany", escape(request_data.get('from_company')))}
                    {soap.soap_helper("FromAddress1", escape(request_data.get('from_address_1')))}
                    {soap.soap_helper("FromAddress2", escape(request_data.get('from_address_2')))}
                    {soap.soap_helper("FromZipCode", request_data.get('from_zip_code'))}
                    {soap.soap_helper("FromCity", escape(request_data.get('from_city')))}
                    {soap.soap_helper("FromState", escape(request_data.get('from_state')))}
                    {soap.soap_helper("FromCountry", escape(request_data.get('from_country')))}
                    {soap.soap_helper("ToName", escape(request_data.get('to_name')))}
                    {soap.soap_helper("ToPhone", escape(request_data.get('to_phone')))}
                    {soap.soap_helper("ToCompany", escape(request_data.get('to_company')))}
                    {soap.soap_helper("ToAddress1", escape(request_data.get('to_address_1')))}
                    {soap.soap_helper("ToAddress2", escape(request_data.get('to_address_2')))}
                    {soap.soap_helper("ToZipCode", request_data.get('to_zip_code'))}
                    {soap.soap_helper("ToCity", escape(request_data.get('to_city')))}
                    {soap.soap_helper("ToState", escape(request_data.get('to_state')))}
                    {soap.soap_helper("ToCountry", escape(request_data.get('to_country')))}
                    {soap.soap_helper("ResidentialDelivery", request_data.get('residential_delivery'))}
                    {soap.soap_helper("Length", request_data.get('length'))}
                    {soap.soap_helper("Width", request_data.get('width'))}
                    {soap.soap_helper("Height", request_data.get('height'))}
                    {soap.soap_helper("Weight", request_data.get('weight'))}
                    {soap.soap_helper("LsoSuppliesUsed", request_data.get('lso_supplies_used'))}
                    {soap.soap_helper("DeclaredValue", request_data.get('declared_value'))}
                    {soap.soap_helper("BillRef", escape(request_data.get('bill_ref')))}
                    {soap.soap_helper("BillRef2", escape(request_data.get('bill_ref_2')))}
                    {soap.soap_helper("BillRef3", escape(request_data.get('bill_ref_3')))}
                    {soap.soap_helper("BillRef4", escape(request_data.get('bill_ref_4')))}
                    {soap.soap_helper("PONumber", request_data.get('po_number'))}
                    {soap.soap_helper("PromoCode", escape(request_data.get('promo_code')))}
                    {soap.soap_helper("OTT", request_data.get('ott'))}
                    {soap.soap_helper("AddSaturdayService", request_data.get('add_saturday_service'))}
                    {soap.soap_helper("EncodeLabel", request_data.get('encode_label'))}
                    {soap.soap_helper("Format", request_data.get('label_format'))}
                    {soap.soap_helper("LabelSize", request_data.get('label_size'))}
                    {soap.soap_helper("HighRes", request_data.get('high_res'))}
                    {soap.soap_helper("ZplBasedImage", request_data.get('zpl_based_image'))}
                    {soap.soap_helper("UseSimple", request_data.get('use_simple'))}
                    {soap.soap_helper("DeliveryNotification", request_data.get('delivery_notification'))}
                    {soap.soap_helper("NotificationEmailAddress", escape(request_data.get('notification_email_address')))}
                    {soap.soap_helper("SignatureRequirement", request_data.get('signature_requirement'))}
                    {soap.soap_helper("SignatureRelease", escape(request_data.get('signature_release')))}
                    {soap.soap_helper("SignatureReleaseName", escape(request_data.get('signature_release_name')))}
                {soap.soap("request", "close")}
            {soap.soap("PrintAirbill", "close")}
        {soap.soap_footer()}
    """

    async with session.post(request_url, data=data, headers=headers) as soap_response:
        response = await soap_response.text()

        if soap_response.status == 200:
            soup = bs4.BeautifulSoup(response, "xml")
            print_air_bill_result = soup.find("PrintAirbillResult")
            return await print_air_bill_parser(print_air_bill_result), "success"
        elif soap_response.status == 500:
            soup = bs4.BeautifulSoup(response, "xml")
            action = soup.find("action")
            if not action:
                return "Check the parameters", "error"
            else:
                return action.get_text(), "error"


async def print_air_bill_parser(print_air_bill_result_xml):
    print_air_bill_dict = dict()

    print_air_bill_dict["estimated_total_charge"] = print_air_bill_result_xml.find("EstimatedTotalCharge").get_text()
    print_air_bill_dict["air_bill_no"] = print_air_bill_result_xml.find("AirbillNo").get_text()
    print_air_bill_dict["service_description"] = print_air_bill_result_xml.find("ServiceDescription").get_text()
    print_air_bill_dict["service_type"] = print_air_bill_result_xml.find("ServiceType").get_text()
    print_air_bill_dict["sort_code"] = print_air_bill_result_xml.find("SortCode").get_text()
    print_air_bill_dict["piece"] = print_air_bill_result_xml.find("Piece").get_text()
    print_air_bill_dict["pieces"] = print_air_bill_result_xml.find("Pieces").get_text()
    print_air_bill_dict["from_name"] = print_air_bill_result_xml.find("FromName").get_text()
    print_air_bill_dict["from_phone"] = print_air_bill_result_xml.find("FromPhone").get_text()
    print_air_bill_dict["from_company"] = print_air_bill_result_xml.find("FromCompany").get_text()
    print_air_bill_dict["from_address_1"] = print_air_bill_result_xml.find("FromAddress1").get_text()
    print_air_bill_dict["from_address_2"] = print_air_bill_result_xml.find("FromAddress2").get_text()
    print_air_bill_dict["from_zip_code"] = print_air_bill_result_xml.find("FromZipCode").get_text()
    print_air_bill_dict["from_city"] = print_air_bill_result_xml.find("FromCity").get_text()
    print_air_bill_dict["from_state"] = print_air_bill_result_xml.find("FromState").get_text()
    print_air_bill_dict["from_country"] = print_air_bill_result_xml.find("FromCountry").get_text()
    print_air_bill_dict["to_name"] = print_air_bill_result_xml.find("ToName").get_text()
    print_air_bill_dict["to_phone"] = print_air_bill_result_xml.find("ToPhone").get_text()
    print_air_bill_dict["to_company"] = print_air_bill_result_xml.find("ToCompany").get_text()
    print_air_bill_dict["to_address_1"] = print_air_bill_result_xml.find("ToAddress1").get_text()
    print_air_bill_dict["to_address_2"] = print_air_bill_result_xml.find("ToAddress2").get_text()
    print_air_bill_dict["to_zip_code"] = print_air_bill_result_xml.find("ToZipCode").get_text()
    print_air_bill_dict["to_city"] = print_air_bill_result_xml.find("ToCity").get_text()
    print_air_bill_dict["to_state"] = print_air_bill_result_xml.find("ToState").get_text()
    print_air_bill_dict["to_country"] = print_air_bill_result_xml.find("ToCountry").get_text()
    print_air_bill_dict["residential_delivery"] = print_air_bill_result_xml.find("ResidentialDelivery").get_text()
    print_air_bill_dict["length"] = print_air_bill_result_xml.find("Length").get_text()
    print_air_bill_dict["width"] = print_air_bill_result_xml.find("Width").get_text()
    print_air_bill_dict["height"] = print_air_bill_result_xml.find("Height").get_text()
    print_air_bill_dict["weight"] = print_air_bill_result_xml.find("Weight").get_text()
    print_air_bill_dict["lso_supplies_used"] = print_air_bill_result_xml.find("LsoSuppliesUsed").get_text()
    print_air_bill_dict["ott"] = print_air_bill_result_xml.find("OTT").get_text()
    print_air_bill_dict["declared_value"] = print_air_bill_result_xml.find("DeclaredValue").get_text()
    print_air_bill_dict["billing_ref"] = print_air_bill_result_xml.find("BillingRef").get_text()
    print_air_bill_dict["billing_ref_2"] = print_air_bill_result_xml.find("BillingRef2").get_text()
    print_air_bill_dict["billing_ref_3"] = print_air_bill_result_xml.find("BillingRef3").get_text()
    print_air_bill_dict["billing_ref_4"] = print_air_bill_result_xml.find("BillingRef4").get_text()
    print_air_bill_dict["signature_requirement"] = print_air_bill_result_xml.find("SignatureRequirement").get_text()
    print_air_bill_dict["label_type"] = print_air_bill_result_xml.find("LabelType").get_text()
    print_air_bill_dict["base_64_data"] = print_air_bill_result_xml.find("Base64data").get_text()

    return print_air_bill_dict
