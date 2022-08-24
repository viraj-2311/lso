from xml.sax.saxutils import escape

import bs4
import requests

from config import Config
from main import soap

headers = {
    "content-type": "text/xml; charset=utf-8",
}


def create_account(requester_first_name='', requester_last_name='', requester_phone='', requester_email='',
                   company_name='', company_phone='', company_phy_address_1='', company_phy_address_2='',
                   company_phy_city='', company_phy_state='', company_phy_zip='', company_bill_address_1='',
                   company_bill_address_2='', company_bill_city='', company_bill_state='', company_bill_zip='',
                   how_hear_about='', login_name='', user_pwd='', comments='', cc_name='', cc_number='',
                   cc_type='', cc_exp_month='', cc_exp_year='', verification_code='', billing_zip='',
                   cc_opt_out='', campaign_name='', campaign_source_code='', referral_code='',
                   number_package_per_day='', business_type='', new_how_hear_about=''):
    request_url = f"https://services.lso.com/partnershippingservices/{Config.SOAP_VERSION}/AccountAdminService.asmx?wsdl"
    data_url = "https://services.lso.com/AccountAdminService/v1_6"
    headers['SoapAction'] = f"{data_url}/CreateNewAccounts"

    data = f"""
        {soap.soap_header(data_url)}
            {soap.soap("CreateNewAccounts")}
                {soap.soap("request")}
                    {soap.soap("AuthenticationInfo")}
                        {soap.soap_helper("Username", Config.SOAP_USER)}
                        {soap.soap_helper("Password", Config.SOAP_PASS)}
                    {soap.soap("AuthenticationInfo", "close")}
                    {soap.soap_helper("PIN", Config.SOAP_PIN)}
                    {soap.soap_helper("RequesterFirstName", escape(requester_first_name))}
                    {soap.soap_helper("RequesterLastName", escape(requester_last_name))}
                    {soap.soap_helper("RequesterPhone", requester_phone)}
                    {soap.soap_helper("RequesterEmail", escape(requester_email))}
                    {soap.soap_helper("CompanyName", escape(company_name))}
                    {soap.soap_helper("CompanyPhone", company_phone)}
                    {soap.soap_helper("CompanyPhyAddress1", escape(company_phy_address_1))}
                    {soap.soap_helper("CompanyPhyAddress2", escape(company_phy_address_2))}
                    {soap.soap_helper("CompanyPhyCity", escape(company_phy_city))}
                    {soap.soap_helper("CompanyPhyState", escape(company_phy_state))}
                    {soap.soap_helper("CompanyPhyZip", company_phy_zip)}
                    {soap.soap_helper("CompanyBillAddress1", escape(company_bill_address_1))}
                    {soap.soap_helper("CompanyBillAddress2", escape(company_bill_address_2))}
                    {soap.soap_helper("CompanyBillCity", escape(company_bill_city))}
                    {soap.soap_helper("CompanyBillState", escape(company_bill_state))}
                    {soap.soap_helper("CompanyBillZip", company_bill_zip)}
                    {soap.soap_helper("HowHearAbout", how_hear_about)}
                    {soap.soap_helper("LoginName", escape(login_name))}
                    {soap.soap_helper("UserPWD", escape(user_pwd))}
                    {soap.soap_helper("Comments", escape(comments))}
                    {soap.soap_helper("CCName", escape(cc_name))}
                    {soap.soap_helper("CCNumber", cc_number)}
                    {soap.soap_helper("CCType", escape(cc_type))}
                    {soap.soap_helper("CCExpMonth", cc_exp_month)}
                    {soap.soap_helper("CCExpYear", cc_exp_year)}
                    {soap.soap_helper("VerificationCode", verification_code)}
                    {soap.soap_helper("BillingZip", billing_zip)}
                    {soap.soap_helper("CCOptOut", cc_opt_out)}
                    {soap.soap_helper("CampaignName", escape(campaign_name))}
                    {soap.soap_helper("CampaignSourceCode", escape(campaign_source_code))}
                    {soap.soap_helper("ReferralCode", escape(referral_code))}
                    {soap.soap_helper("NumberPackagesPerDay", escape(number_package_per_day))}
                    {soap.soap_helper("BusinessType", escape(business_type))}
                    {soap.soap_helper("NewHowHearAbout", escape(new_how_hear_about))}
                {soap.soap("request", "close")}
            {soap.soap("CreateNewAccounts", "close")}
        {soap.soap_footer()}
    """

    response = requests.post(request_url, data=data, headers=headers)
    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, "xml")
        create_account_result = soup.find("CreateNewAccountsResult")
        if create_account_result.find('Success').text == 'true':
            return parse_account_info(create_account_result), "success"
        else:
            if 'CustContactPhone' in create_account_result.find('string').get_text():
                return "Phone number must be 10 digit", "error"
            elif 'LoginName' in create_account_result.find('string').get_text():
                return "Login name too long", "error"
    elif response.status_code == 500:
        soup = bs4.BeautifulSoup(response.text, "xml")
        action = soup.find("action")
        if not action:
            return "Check the parameters", "error"
        else:
            return action.get_text(), "error"


def parse_account_info(account_info_xml):
    account_info_dict = dict()
    account_info_dict['customer_id'] = account_info_xml.find("CustomerId").get_text()
    account_info_dict['LoginName'] = account_info_xml.find("LoginName").get_text()
    return account_info_dict
