from xml.sax.saxutils import escape

import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8"
}


def schedule_pickup(account_number, phone_number, extension, pickup_requestor_name, company_name, line_1, line_2,
                    line_3, city, state, zip_code, country, pickup_date, pickup_ready_time, business_close_time,
                    left_outside_door_after_close_time, dolly_required, number_of_packages, total_weight,
                    special_instructions, hippa_pickup):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/PickupService.asmx?WSDL"
    data_url = "https://services.lso.com/PickupService/v1_6"
    headers["SoapAction"] = f"{data_url}/SchedulePickup"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("SchedulePickup")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("Customer")}
                        {soap.soap_helper("AccountNumber", account_number)}
                    {soap.soap("Customer", "close")}
                    {soap.soap_helper("PhoneNumber", phone_number)}
                    {soap.soap_helper("Extension", extension)}
                    {soap.soap_helper("PickupRequestorName", escape(pickup_requestor_name))}
                    {soap.soap_helper("CompanyName", escape(company_name))}
                    {soap.soap("PickupAddress")}
                        {soap.soap_helper("Line1", escape(line_1))}
                        {soap.soap_helper("Line2", escape(line_2))}
                        {soap.soap_helper("Line3", escape(line_3))}
                        {soap.soap_helper("City", escape(city))}
                        {soap.soap_helper("State", escape(state))}
                        {soap.soap_helper("ZipCode", escape(zip_code))}
                        {soap.soap_helper("Country", escape(country))}
                    {soap.soap("PickupAddress", "close")}
                    {soap.soap_helper("PickupDate", pickup_date)}
                    {soap.soap_helper("PickupReadyTime", pickup_ready_time)}
                    {soap.soap_helper("BusinessCloseTime", business_close_time)}
                    {soap.soap_helper("LeftOutsideDoorAfterCloseTime", left_outside_door_after_close_time)}
                    {soap.soap_helper("DollyRequired", dolly_required)}
                    {soap.soap_helper("NumberOfPackages", number_of_packages)}
                    {soap.soap_helper("TotalWeight", total_weight)}
                    {soap.soap_helper("SpecialInstructions", special_instructions)}
                    {soap.soap_helper("HippaPickup", hippa_pickup)}
                {soap.soap("request", "close")}
            {soap.soap("SchedulePickup", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        schedule_pickup_result = soup.find("SchedulePickupResult")
        return parse_schedule_pickup_info(schedule_pickup_result), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_schedule_pickup_info(schedule_pickup_data_xml):
    schedule_pickup_info_dict = dict()
    schedule_pickup_info_dict["confirmation_number"] = schedule_pickup_data_xml.find("ConfirmationNumber").get_text()
    schedule_pickup_info_dict["phone_number"] = schedule_pickup_data_xml.find("PhoneNumber").get_text()
    schedule_pickup_info_dict["extension"] = schedule_pickup_data_xml.find("Extension").get_text()
    schedule_pickup_info_dict["pickup_requestor_name"] = schedule_pickup_data_xml.find("PickupRequestorName").get_text()
    schedule_pickup_info_dict["company_name"] = schedule_pickup_data_xml.find("CompanyName").get_text()
    schedule_pickup_info_dict["pickup_address"] = dict()
    schedule_pickup_info_dict["pickup_address"]["line_1"] = schedule_pickup_data_xml.find("Line1").get_text()
    schedule_pickup_info_dict["pickup_address"]["line_2"] = schedule_pickup_data_xml.find("Line2").get_text()
    schedule_pickup_info_dict["pickup_address"]["line_3"] = schedule_pickup_data_xml.find("Line3").get_text()
    schedule_pickup_info_dict["pickup_address"]["city"] = schedule_pickup_data_xml.find("City").get_text()
    schedule_pickup_info_dict["pickup_address"]["state"] = schedule_pickup_data_xml.find("State").get_text()
    schedule_pickup_info_dict["pickup_address"]["zip_code"] = schedule_pickup_data_xml.find("ZipCode").get_text()
    schedule_pickup_info_dict["pickup_address"]["country"] = schedule_pickup_data_xml.find("Country").get_text()
    schedule_pickup_info_dict["pickup_date"] = schedule_pickup_data_xml.find("PickupDate").get_text()
    schedule_pickup_info_dict["pickup_ready_time"] = schedule_pickup_data_xml.find("PickupReadyTime").get_text()
    schedule_pickup_info_dict["business_close_time"] = schedule_pickup_data_xml.find("BusinessCloseTime").get_text()
    schedule_pickup_info_dict["left_outside_door_after_close_time"] = schedule_pickup_data_xml.find(
        "LeftOutsideDoorAfterCloseTime").get_text()
    schedule_pickup_info_dict["dolly_required"] = schedule_pickup_data_xml.find("DollyRequired").get_text()
    schedule_pickup_info_dict["number_of_packages"] = schedule_pickup_data_xml.find("NumberOfPackages").get_text()
    schedule_pickup_info_dict["total_weight"] = schedule_pickup_data_xml.find("TotalWeight").get_text()
    schedule_pickup_info_dict["special_instructions"] = schedule_pickup_data_xml.find("SpecialInstructions").get_text()
    schedule_pickup_info_dict["hippa_pickup"] = schedule_pickup_data_xml.find("HippaPickup").get_text()

    return schedule_pickup_info_dict


def cancel_pickup_service(account_number, confirmation_number):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/PickupService.asmx?WSDL"
    data_url = "https://services.lso.com/PickupService/v1_6"
    headers["SoapAction"] = f"{data_url}/CancelPickup"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("CancelPickup")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("Customer")}
                        {soap.soap_helper("AccountNumber", account_number)}
                    {soap.soap("Customer", "close")}
                    {soap.soap_helper("ConfirmationNumber", confirmation_number)}
                {soap.soap("request", "close")}
            {soap.soap("CancelPickup", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        return "canceled"
    if response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def get_pickup_dates(account_number=None, phone_number=None, extension=None, zip_code=None, time_format=None):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/Pickup2Service.asmx?WSDL"
    data_url = "https://services.lso.com/Pickup2Service/v1_6"
    headers["SoapAction"] = f"{data_url}/GetPickupDays"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("GetPickupDays")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap_helper("CustID", account_number)}
                    {soap.soap_helper("PhoneNumber", phone_number)}
                    {soap.soap_helper("Extension", extension)}
                    {soap.soap_helper("Zipcode", zip_code)}
                    {soap.soap_helper("TimeFormat", time_format)}
                {soap.soap("request", "close")}
            {soap.soap("GetPickupDays", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        pickup_dates = soup.findAll("PickupDate")
        return parse_pickup_dates(pickup_dates), "success"
    if response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return "Check the parameters", "error"


def parse_pickup_dates(pickup_dates_xml):
    pickup_dates_list = []
    for pickup_date in pickup_dates_xml:
        pickup_dates_dict = dict()
        pickup_dates_dict["date_of_pickup"] = pickup_date.find("DateOfPickup").get_text()
        ready_time = pickup_date.find("ReadyTimes").findAll("string")
        close_time = pickup_date.find("CloseTimes").findAll("string")
        pickup_dates_dict["ready_time"] = dict()
        pickup_dates_dict["close_time"] = dict()
        ready_time_list = []
        close_time_list = []
        for time in ready_time:
            ready_time_list.append(time.get_text())

        for time in close_time:
            close_time_list.append(time.get_text())

        pickup_dates_dict["ready_time"] = ready_time_list
        pickup_dates_dict["close_time"] = close_time_list

        pickup_dates_list.append(pickup_dates_dict)

    return pickup_dates_list
