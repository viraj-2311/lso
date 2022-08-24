from xml.sax.saxutils import escape

import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8",
}


def fuel_surcharge(method_name="Fsc", search_value=None):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/AccountAdminService.asmx"
    data_url = "https://services.lso.com/AccountAdminService/v1_6"
    headers["SoapAction"] = f"{data_url}/GetRowData"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("GetRowData")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap_helper("PIN", Config.SOAP_PIN)}
                    {soap.soap_helper("MethodName", escape(method_name))}
                    {soap.soap_helper("SearchValue", escape(search_value))}
                {soap.soap("request", "close")}
            {soap.soap("GetRowData", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)

    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        success = soup.find("Success").get_text()
        if success == "true":
            array_of_cell_string = soup.find_all("ArrayOfCellOfStringString")

            data_dict = dict()
            data_dict["exp"] = []
            data_dict["gnd"] = []

            for array_of_cell in array_of_cell_string:
                cell_data_dict = dict()
                cell_of_string = array_of_cell.find_all("CellOfStringString")
                for cell in cell_of_string:
                    if cell.find("Column").get_text() == "CompanyName":
                        cell_data_dict["company_name"] = cell.find("Value").get_text()
                    elif cell.find("Column").get_text() == "ShortName":
                        cell_data_dict["short_name"] = cell.find("Value").get_text()
                    elif cell.find("Column").get_text() == "Description":
                        cell_data_dict["description"] = cell.find("Value").get_text()
                    elif cell.find("Column").get_text() == "Amount":
                        cell_data_dict["amount"] = cell.find("Value").get_text()
                    elif cell.find("Column").get_text() == "StartDate":
                        cell_data_dict["start_date"] = cell.find("Value").get_text()
                    elif cell.find("Column").get_text() == "Enabled":
                        cell_data_dict["enabled"] = cell.find("Value").get_text()

                if cell_data_dict["short_name"] == "FSCEXP":
                    data_dict["exp"].append(cell_data_dict)
                elif cell_data_dict["short_name"] == "FSCGND":
                    data_dict["gnd"].append(cell_data_dict)

            return data_dict, "success"
        else:
            return {}, "error"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"
