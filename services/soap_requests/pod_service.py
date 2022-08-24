from xml.sax.saxutils import escape

import bs4
import requests

from config import Config
from main import soap
from utilities import get_soap_text

headers = {
    "content-type": "text/xml; charset=utf-8",
}


def air_bill_number_helper(air_bill_number):
    soap_data = f"""
                {soap.soap_helper("string", air_bill_number)}
            """
    return soap_data


def pod_info(cust_id=None, uid=None, login_name=None, air_bill_number=None):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/AccountAdminService.asmx"
    data_url = "https://services.lso.com/AccountAdminService/v1_6"
    headers["SoapAction"] = f"{data_url}/GetPODInfo"

    data = f"""
            {soap.soap_header(data_url)}
                {soap.soap("GetPODInfo")}
                    {soap.soap("request")}
                        {soap.soap("AuthenticationInfo")}
                            {soap.soap_helper("Username", Config.SOAP_USER)}
                            {soap.soap_helper("Password", Config.SOAP_PASS)}
                        {soap.soap("AuthenticationInfo", "close")}
                        {soap.soap_helper("PIN", Config.SOAP_PIN)}
                        {soap.soap_helper("CustID", cust_id)}
                        {soap.soap_helper("UID", uid)}
                        {soap.soap_helper("loginname", escape(login_name))}
                        {soap.soap("AirbillNoList")}
                            {air_bill_number_helper(air_bill_number)}
                        {soap.soap("AirbillNoList", "close")}
                    {soap.soap("request", "close")}
                {soap.soap("GetPODInfo", "close")}
            {soap.soap_footer()}
       """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        pod_info_list = soup.find_all("PODInfo")
        parsed_pod_info = parse_pod_info(pod_info_list)
        if not parsed_pod_info:
            return "No Data", "error"
        else:
            return parsed_pod_info, "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_pod_info(pod_info_list_xml):
    pod_info_list = []
    for info in pod_info_list_xml:
        try:
            pod_info_dict = dict()
            pod_info_dict["air_bill_no"] = get_soap_text(info, "Airbillno")
            pod_info_dict["success"] = get_soap_text(info, "Success")
            pod_info_dict["tracking_status_description"] = get_soap_text(info, "TrackingStatusDescription")
            pod_info_dict["delivery_date"] = get_soap_text(info, "DeliveryDate")
            pod_info_dict["pickup_date"] = get_soap_text(info, "PickupDate")
            pod_info_dict["signed_by"] = get_soap_text(info, "SignedBy")
            pod_info_dict["delivered_to"] = get_soap_text(info, "DeliveredTo")
            pod_info_dict["billing_ref"] = get_soap_text(info, "BillingRef")
            pod_info_dict["billing_ref_2"] = get_soap_text(info, "BillingRef2")
            pod_info_dict["billing_ref_3"] = get_soap_text(info, "BillingRef3")
            pod_info_dict["billing_ref_4"] = get_soap_text(info, "BillingRef4")
            pod_info_dict["pkg_user_2"] = get_soap_text(info, "PkgUser3")
            pod_info_dict["pkg_user_4"] = get_soap_text(info, "PkgUser4")
            pod_info_dict["from_attn_name"] = get_soap_text(info, "FromAttnName")
            pod_info_dict["from_company_name"] = get_soap_text(info, "FromCompanyName")
            pod_info_dict["from_address_1"] = get_soap_text(info, "FromAddress1")
            pod_info_dict["from_address_2"] = get_soap_text(info, "FromAddress2")
            pod_info_dict["from_city"] = get_soap_text(info, "FromCity")
            pod_info_dict["from_state"] = get_soap_text(info, "FromState")
            pod_info_dict["from_zip"] = get_soap_text(info, "FromZip")
            pod_info_dict["to_attn_name"] = get_soap_text(info, "ToAttnName")
            pod_info_dict["to_company_name"] = get_soap_text(info, "ToCompanyName")
            pod_info_dict["to_address_1"] = get_soap_text(info, "ToAddress1")
            pod_info_dict["to_address_2"] = get_soap_text(info, "ToAddress2")
            pod_info_dict["to_city"] = get_soap_text(info, "ToCity")
            pod_info_dict["to_state"] = get_soap_text(info, "ToState")
            pod_info_dict["to_zip"] = get_soap_text(info, "ToZip")
            pod_info_dict["image_available"] = get_soap_text(info, "ImageAvailable")
            pod_info_dict["signature_img"] = get_soap_text(info, "SignatureImg")
            pod_info_dict["signature_format"] = get_soap_text(info, "SignatureFormat")
            pod_info_dict["pod_photos_found"] = get_soap_text(info, "PODPhotosFound")

            pod_info_list.append(pod_info_dict)
        except AttributeError:
            continue
    return pod_info_list
