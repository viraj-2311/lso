import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8"
}


def retrieve_service_types():
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/ShippingService.asmx"
    data_url = "https://services.lso.com/ShippingService/v1_6"
    headers["SoapAction"] = f"{data_url}/RetrieveServiceTypes"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("RetrieveServiceTypes")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                {soap.soap("request", "close")}
            {soap.soap("RetrieveServiceTypes", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        service_types_info = soup.find_all("ServiceTypeInfo")
        return parse_service_types(service_types_info), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_service_types(service_type_info_xml):
    service_types_list = []
    for info in service_type_info_xml:
        service_types_dict = dict()
        service_types_dict["description"] = info.find("Description").get_text()
        service_types_dict["service_type"] = info.find("ServiceType").get_text()
        service_types_dict["can_require_business_signature"] = info.find("CanRequireBusinessSignature").get_text()
        service_types_dict["can_require_residential_signature"] = info.find("CanRequireResidentialSignature").get_text()
        service_types_dict["inside_in"] = info.find("InsideIn").get_text()
        service_types_dict["outside_out"] = info.find("OutsideOut").get_text()
        service_types_dict["inside_out"] = info.find("InsideOut").get_text()
        service_types_dict["outside_in"] = info.find("OutsideIn").get_text()

        service_types_list.append(service_types_dict)

    return service_types_list


def retrieve_service_type_by_zip_code(from_zip, to_zip):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/ShippingService.asmx"
    data_url = "https://services.lso.com/ShippingService/v1_6"
    headers["SoapAction"] = f"{data_url}/GetServiceTypesByZip"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("GetServiceTypesByZip")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap_helper("FromZip", from_zip)}
                    {soap.soap_helper("ToZip", to_zip)}
                {soap.soap("request", "close")}
            {soap.soap("GetServiceTypesByZip", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        service_types_info = soup.find_all("ServiceTypeInfo")
        return parse_service_types(service_types_info), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def check_zip(from_zip=None, to_zip=None):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/AccountAdminService.asmx"
    data_url = "https://services.lso.com/AccountAdminService/v1_6"
    headers["SoapAction"] = f"{data_url}/GetZone"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("GetZone")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap_helper("FromZip", from_zip)}
                    {soap.soap_helper("ToZip", to_zip)}
                {soap.soap("request", "close")}
            {soap.soap("GetZone", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        zone = soup.find("Zone").get_text()
        if zone == "No Service for From Zip" or zone == "No Service for To Zip":
            return "false", "error"
        else:
            return "true", "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        return soup.find("action").get_text(), "error"
