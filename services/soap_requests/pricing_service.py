import datetime

import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8",
}


def estimate_price(account_number=0, from_zip_code=0, service_type=0, to_zip_code=0, to_country="UnitedStates",
                   weight=0, declared_value=0, length=0, height=0, pickup="false", residential_delivery="false",
                   lso_supplies_used="false", ship_date=datetime.date.today(), signature_requirement="None",
                   width=0, hippa="false", use_simple_pricing="false"):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/PricingService.asmx?WSDL"
    data_url = "https://services.lso.com/PricingService/v1_6"
    headers["SoapAction"] = f"{data_url}/EstimatePrice"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("EstimatePrice")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("Customer")}
                        {soap.soap_helper("AccountNumber", account_number)}
                    {soap.soap("Customer", "close")}
                    {soap.soap_helper("ServiceType", service_type)}
                    {soap.soap_helper("FromZipCode", from_zip_code)}
                    {soap.soap_helper("ToZipCode", to_zip_code)}
                    {soap.soap_helper("ToCountry", to_country)}
                    {soap.soap_helper("Weight", weight)}
                    {soap.soap_helper("DeclaredValue", declared_value)}
                    {soap.soap_helper("Length", length)}
                    {soap.soap_helper("Width", width)}
                    {soap.soap_helper("Height", height)}
                    {soap.soap_helper("Pickup", pickup)}
                    {soap.soap_helper("ResidentialDelivery", residential_delivery)}
                    {soap.soap_helper("LsoSuppliesUsed", lso_supplies_used)}
                    {soap.soap_helper("ShipDate", ship_date)}
                    {soap.soap_helper("SignatureRequirement", signature_requirement)}
                    {soap.soap_helper("Hippa", hippa)}
                    {soap.soap_helper("UseSimplePricing", use_simple_pricing)}
                {soap.soap("request", "close")}
            {soap.soap("EstimatePrice", "close")}
        {soap.soap_footer()} 
    """
    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        estimate_price_result = soup.find_all("EstimatePriceResult")
        return parse_estimate_price(estimate_price_result), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_estimate_price(estimate_price_xml):
    estimate_price_info_dict = dict()
    for info in estimate_price_xml:
        estimate_price_info_dict['base_price'] = info.find('BasePrice').get_text()
        estimate_price_info_dict['service_charge'] = info.find('ServiceCharge').get_text()
        estimate_price_info_dict['additional_insurance_charge'] = info.find('AdditionalInsuranceCharge').get_text()
        estimate_price_info_dict['fuel_surcharge'] = info.find('FuelSurcharge').get_text()
        estimate_price_info_dict['supply_usage_fee'] = info.find('SupplyUsageFee').get_text()
        estimate_price_info_dict['pickup_fee'] = info.find('PickupFee').get_text()
        estimate_price_info_dict['residential_delivery_fee'] = info.find('ResidentialDeliveryFee').get_text()
        estimate_price_info_dict['total_charge'] = info.find('TotalCharge').get_text()
        estimate_price_info_dict['expected_delivery_date'] = info.find('ExpectedDeliveryDate').get_text()
        estimate_price_info_dict['discount'] = info.find('Discount').get_text()
        estimate_price_info_dict['signature_fee'] = info.find('SignatureFee').get_text()
        estimate_price_info_dict['remote_delivery_fee'] = info.find('RemoteDeliveryFee').get_text()
        estimate_price_info_dict['hippa_fee'] = info.find('HippaFee').get_text()
        estimate_price_info_dict['zone'] = info.find('Zone').get_text()

    return estimate_price_info_dict


def estimate_multiple_prices(request_data_list):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/PricingService.asmx?WSDL"
    data_url = "https://services.lso.com/PricingService/v1_6"
    headers["SoapAction"] = f"{data_url}/EstimateMultiplePrices"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("EstimateMultiplePrices")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap("RequestData")}
                        {request_data_helper(request_data_list)}
                    {soap.soap("RequestData", "close")}
                {soap.soap("request", "close")}
            {soap.soap("EstimateMultiplePrices", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        estimate_multiple_response_data = soup.find_all("EstimateMultipleResponseData")
        return parse_multiple_response_data(estimate_multiple_response_data), "success"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def request_data_helper(request_data):
    soap_data_final = ""
    for data in request_data:
        soap_data = f"""
            {soap.soap("EstimatePriceRequestData")}
                {soap.soap("Customer")}
                    {soap.soap_helper("AccountNumber", data.get("account_number", ""))}
                {soap.soap("Customer", "close")}
                {soap.soap_helper("ServiceType", data.get("service_type", ""))}
                {soap.soap_helper("FromZipCode", data.get("from_zip_code", ""))}
                {soap.soap_helper("ToZipCode", data.get("to_zip_code", ""))}
                {soap.soap_helper("ToCountry", data.get("to_country", ""))}
                {soap.soap_helper("Weight", data.get("weight", ""))}
                {soap.soap_helper("DeclaredValue", data.get("declared_value", ""))}
                {soap.soap_helper("Length", data.get("length", ""))}
                {soap.soap_helper("Width", data.get("width", ""))}
                {soap.soap_helper("Height", data.get("height", ""))}
                {soap.soap_helper("Pickup", data.get("pickup", ""))}
                {soap.soap_helper("ResidentialDelivery", data.get("residential_delivery", ""))}
                {soap.soap_helper("LsoSuppliesUsed", data.get("lso_supplies_used", ""))}
                {soap.soap_helper("ShipDate", data.get("ship_date", ""))}
                {soap.soap_helper("SignatureRequirement", data.get("signature_requirement", ""))}
                {soap.soap_helper("Hippa", data.get("hippa", ""))}
                {soap.soap_helper("UseSimplePricing", data.get("use_simple_pricing", ""))}
            {soap.soap("EstimatePriceRequestData", "close")}
        """
        soap_data_final += soap_data
    return soap_data_final


def parse_multiple_response_data(response_data_xml):
    multiple_response_data_list = []
    for info in response_data_xml:
        multiple_response_data_dict = dict()
        multiple_response_data_dict['base_price'] = info.find('BasePrice').get_text()
        multiple_response_data_dict['service_charge'] = info.find('ServiceCharge').get_text()
        multiple_response_data_dict['additional_insurance_charge'] = info.find('AdditionalInsuranceCharge').get_text()
        multiple_response_data_dict['fuel_surcharge'] = info.find('FuelSurcharge').get_text()
        multiple_response_data_dict['supply_usage_fee'] = info.find('SupplyUsageFee').get_text()
        multiple_response_data_dict['pickup_fee'] = info.find('PickupFee').get_text()
        multiple_response_data_dict['residential_delivery_fee'] = info.find('ResidentialDeliveryFee').get_text()
        multiple_response_data_dict['total_charge'] = info.find('TotalCharge').get_text()
        multiple_response_data_dict['expected_delivery_date'] = info.find('ExpectedDeliveryDate').get_text()
        multiple_response_data_dict['discount'] = info.find('Discount').get_text()
        multiple_response_data_dict['signature_fee'] = info.find('SignatureFee').get_text()
        multiple_response_data_dict['remote_delivery_fee'] = info.find('RemoteDeliveryFee').get_text()
        multiple_response_data_dict['hippa_fee'] = info.find('HippaFee').get_text()
        multiple_response_data_dict['zone'] = info.find('Zone').get_text()
        multiple_response_data_dict['priced_successfully'] = info.find('PricedSuccessfully').get_text()
        multiple_response_data_dict['error_code'] = info.find('ErrorCode').get_text()

        multiple_response_data_list.append(multiple_response_data_dict)

    return multiple_response_data_list
