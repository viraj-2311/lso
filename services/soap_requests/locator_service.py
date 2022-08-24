import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8",
}


def retrieve_drop_boxes():
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/LocatorService.asmx?WSDL"
    data_url = "https://services.lso.com/LocatorService/v1_6"
    headers["SoapAction"] = f"{data_url}/RetrieveDropBoxes"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("RetrieveDropBoxes")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                {soap.soap("request", "close")}
            {soap.soap("RetrieveDropBoxes", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        drop_box_info = soup.find_all("DropBoxInfo")
        return parse_drop_box_info(drop_box_info), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_drop_box_info(drop_box_info_xml):
    drop_box_info_list = []
    for info in drop_box_info_xml:
        drop_box_info_dict = dict()
        drop_box_info_dict['building_or_office_park'] = info.find("BuildingOrOfficePark").get_text()
        drop_box_info_dict['detailed_location_desc'] = info.find("DetailedLocationDescription").get_text()
        drop_box_info_dict['physical_address'] = dict()
        drop_box_info_dict['physical_address']['line_1'] = info.find("Line1").get_text()
        drop_box_info_dict['physical_address']['line_2'] = info.find("Line2").get_text()
        drop_box_info_dict['physical_address']['city'] = info.find("City").get_text()
        drop_box_info_dict['physical_address']['state'] = info.find("State").get_text()
        drop_box_info_dict['physical_address']['zip_code'] = info.find("ZipCode").get_text()
        drop_box_info_dict['physical_address']['country'] = info.find("Country").get_text()
        drop_box_info_dict['pickup_time'] = info.find("PickupTime").get_text()
        drop_box_info_dict['latitude'] = info.find("Latitude").get_text()
        drop_box_info_dict['longitude'] = info.find("Longitude").get_text()

        drop_box_info_list.append(drop_box_info_dict)

    return drop_box_info_list


def retrieve_service_areas(account_number, zip_code_filter, origin_zip, country_filter):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/LocatorService.asmx?WSDL"
    data_url = "https://services.lso.com/LocatorService/v1_6"

    headers["SoapAction"] = f"{data_url}/RetrieveServiceAreas"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("RetrieveServiceAreas")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("Customer")}
                        {soap.soap_helper("AccountNumber", account_number)}
                    {soap.soap("Customer", "close")}
                    {soap.soap_helper("FilteredSearch", "true")}
                    {soap.soap_helper("ZipCodeFilter", zip_code_filter)}
                    {soap.soap_helper("OriginZip", origin_zip)}
                    {soap.soap_helper("CountryFilter", country_filter)}
                {soap.soap("request", "close")}
            {soap.soap("RetrieveServiceAreas", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        service_areas = soup.find_all("ServiceArea")
        return parse_service_areas(service_areas), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_service_areas(service_areas):
    service_area_info_list = []
    for info in service_areas:
        service_area_info_dict = dict()
        service_area_info_dict["zip_code"] = info.find("ZipCode").get_text()
        service_area_info_dict["country"] = info.find("Country").get_text()
        service_area_info_dict["city_code"] = info.find("CityCode").get_text()
        service_area_info_dict["city_name"] = info.find("CityName").get_text()
        service_area_info_dict["state"] = info.find("State").get_text()
        service_area_info_dict["same_day_pickup_cutoff_time"] = info.find("SameDayPickupCutOffTime").get_text()
        service_area_info_dict["last_pickup_time"] = info.find("LastPickupTime").get_text()
        service_area_info_dict["available_service_types"] = [types.get_text() for types in info.find_all("ServiceType")]
        service_area_info_dict["basic_service_commitment_time"] = info.find("BasicServiceCommitmentTime").get_text()
        service_area_info_dict["delivery_location"] = info.find("DeliveryLocation").get_text()
        service_area_info_dict["core"] = info.find("Core").get_text()
        service_area_info_dict["ecommerce_pricing_available"] = info.find("ECommercePricingAvailable").get_text()

        service_area_info_list.append(service_area_info_dict)

    return service_area_info_list
