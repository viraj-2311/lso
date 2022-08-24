import datetime
import re
from functools import wraps
from http import HTTPStatus

from flask import request, render_template, Response
from pymssql import _mssql
import boto3
from botocore.exceptions import ClientError

from config import Config

from main import app_db, ops_db, service_manager, CustomError


def strip_specials(text_string):
    switcher = {
        "'": True,
        "&": True,
        "%": True,
        "=": True,
        chr(34): True,
        chr(92): True,
    }

    output_string = ''
    for char in text_string:
        temp = switcher.get(char, '')
        if temp:
            output_string += ''
        else:
            output_string += char

    return output_string


def custom_response(status, message, code, data=None):
    if not isinstance(data, type(None)):
        return {"status": status, "message": message, "data": data}, code
    else:
        return {"status": status, "message": message}, code


def validate_email(email):
    pattern = "^([a-zA-Z0-9_+\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$"

    match = re.search(pattern, email)

    if match:
        return True


def validate_phone(phone):
    if not phone:
        return False
    else:
        phone = phone.replace("(", "")
        phone = phone.replace(")", "")
        phone = phone.replace("-", "")
        phone = phone.replace(" ", "")
        phone = phone.replace(".", "")
        phone = phone.replace("+", "")

        if len(phone) > 20:
            phone = phone[:20]

        if len(phone) == 10:
            if phone.isnumeric():
                return phone
            else:
                return False
        else:
            return False


def validate_zip(zip_code):
    if not zip_code:
        return False
    else:
        zip_code = zip_code.replace(" ", "")
        zip_code = zip_code.replace("-", "")

        if zip_code.isnumeric() and len(zip_code) == 5:
            return True
        else:
            return False


def get_city_state_func(zip_code, country, account_number=None, user_id=None):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)
    try:
        get_city_state_query = f"EXEC sp_getCityState '{zip_code}', '{country}'"

        if option_visible("AllowNoSvcFromZip", cust_id=account_number, user_id=user_id):
            get_city_state_query += ", '1'"
        app_db.execute_query(cursor, get_city_state_query)
        get_city_state = cursor.fetchall()[0]
        if not get_city_state:
            return False
        else:
            return get_city_state
    except (_mssql.MssqlDatabaseException, IndexError) as e:
        return False


def zip_inside_core_service_area(zip_code):
    conn = ops_db.create_connection()
    cursor = ops_db.create_cursor(conn)
    try:
        core_by_zip_query = f"SELECT Core FROM ServiceByZipCode WHERE ZipCode='{zip_code}'"
        ops_db.execute_query(cursor, core_by_zip_query)
        core_by_zip = cursor.fetchall()
        if not core_by_zip:
            return False
        return True
    except _mssql.MssqlDatabaseException:
        return False
    finally:
        ops_db.close_connection(conn)


def service_allowed_override(from_zip, to_zip):
    conn = ops_db.create_connection()
    cursor = ops_db.create_cursor(conn)
    try:
        service_allowed_query = f"SELECT S.ServiceID Service, A.ServiceID Allowed, A.ServiceDenied " \
                                f"FROM StdServiceType S LEFT OUTER JOIN (SELECT ServiceID, COALESCE(ServiceDenied, 0)" \
                                f" as ServiceDenied FROM AllowedServiceByZip WHERE FromZip = '{from_zip}'" \
                                f" AND ToZip = '{to_zip}' AND COALESCE(Disabled, 0) = 0) A ON S.ServiceID = A.ServiceID"
        ops_db.execute_query(cursor, service_allowed_query)

        service_allowed = cursor.fetchall()

        allowed_services = dict()

        for services in service_allowed:
            service = services["Service"]
            allowed = services["Allowed"]
            denied = services["ServiceDenied"]
            if denied == 1:
                allowed_services[service] = 2
            elif not allowed:
                allowed_services[service] = 1
            else:
                allowed_services[service] = False

        return allowed_services
    except _mssql.MssqlDatabaseException:
        return {}
    finally:
        ops_db.close_connection(conn)


service_type_dict = {
    "LSO Priority Next Day": "PriorityBasic",
    "LSO Priority Overnight": "PriorityBasic",
    "LSO Early Overnight": "PriorityEarly",
    "LSO Economy Next Day": "GroundEarly",
    "LSO Saturday": "PrioritySaturday",
    "LSO 2nd Day": "Priority2ndDay",
    "Noon Delivery": "PriorityNoon",
    "LSO Plus": "LSOPlus",
    "LSO Ground": "GroundBasic",
    "LSO Mexico": "Mexico",
    "Same Day ": "SameDay",
    "FedEx": "FedEx",
    "Other Delivery": "Other",
    "LSO ECommerce": "ECommerce",
}


def mail_body(account_number=None, from_email=None, from_name=None, from_company=None, from_phone=None,
              from_address_1=None,
              from_address_2=None, from_city=None, from_zip=None, to_name=None, to_company=None, to_phone=None,
              to_address_1=None, to_address_2=None, to_city=None, to_zip=None, billing_reference=None,
              letter_pack_quantity=None, tube_quantity=None, plastic_polypak_quantity=None,
              webship_air_bill_pouches_quantity=None, pre_printed_air_bill_quantity=None, green_abs_quantity=None,
              large_cardboard_box_quantity=None, medium_cardboard_box_quantity=None, small_cardboard_box_quantity=None,
              service_type_on_air_bill=None):
    return f"""       Lone Star Overnight - Supply Order Form 
       ---------------------------------------
     
 Account Number:  {account_number}
         E-mail:  {from_email}
         
 FROM SIDE OF AB
 ---------------
       FromName:  {from_name}
   Company Name:  {from_company}
          Phone:  {from_phone}
       Address1:  {from_address_1}
       Address2:  {from_address_2}
           City:  {from_city}
            Zip:  {from_zip}
            
 TO SIDE OF AB
 -------------
         ToName:  {to_name}
   Company Name:  {to_company}
          Phone:  {to_phone}
       Address1:  {to_address_1}
       Address2:  {to_address_2}
           City:  {to_city}
            Zip:  {to_zip}
 
 BILLING REFERENCE
 -----------------
    Billing Ref:  {billing_reference}
    
 SUPPLIES NEEDED
 ---------------
   Letter Packs:  {letter_pack_quantity}
   Tubes:  {tube_quantity}
   Poly Bags:  {plastic_polypak_quantity}
   WebShip Pouches:  {webship_air_bill_pouches_quantity}
   Blue ABs:  {pre_printed_air_bill_quantity}
   Green ABs:  {green_abs_quantity}
   Large Boxes:  {large_cardboard_box_quantity}
   Medium Boxes:  {medium_cardboard_box_quantity}
   Small Boxes:  {small_cardboard_box_quantity}
   Service Types:  {service_type_on_air_bill}

   Source Form:  SupplyRequest"""


def validate_weight(weight, service_type):
    if not weight:
        return "enter valid weight", False
    if not weight.isnumeric():
        return "enter valid weight", False

    if service_type == "M":
        if not weight.isnumeric():
            return "All the Maxico shipments require a weight to be entered.", False

        if float(weight) < 0.5 or float(weight) > 10:
            return "All Mexico shipments must be between 0.5 - 10 lbs", False

    if (float(weight) < 0 or float(weight) > 150) and "G,B,E,S,V".find(service_type) >= 0:
        return "Valid Priority weights are 0.5 - 150 lbs.", False

    if (float(weight) < 0 or float(weight) > 150) and "W,T".find(service_type) >= 0:
        return "Valid Ground weights are 1 - 150 lbs.", False

    return "Valid", True


def convert_base_10(air_bill_number, base_digits):
    global i
    last_i = 1
    s = ""
    base_size = len(base_digits)
    while int(air_bill_number) != 0:
        tmp = int(air_bill_number)
        i = 0
        while tmp >= base_size:
            i += 1
            tmp = tmp / base_size

        if i != last_i - 1 and last_i != 0:
            s = s + (chr(int(base_digits[0])) * (last_i - i - 1))
        tmp = int(tmp)
        s = s + base_digits[tmp + 1: -(len(base_digits) - (tmp + 1) - 1)]
        air_bill_number = int(air_bill_number) - tmp * (base_size ** i)
        last_i = i
    s = s + (chr(int(base_digits[0])) * i)
    return s


def pad_air_bill(air_bill_number, ab_type):
    global prefix
    max_len = 8
    temp = str(air_bill_number).strip()

    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)

    try:
        prefix_query = f"SELECT ExpressABPrefix, GroundABPrefix, MexicoABPrefix FROM WebControl WHERE ControlNo='LSO'"
        app_db.execute_query(cursor, prefix_query)
        prefixes = cursor.fetchall()[0]
        if ab_type == 0:
            prefix = prefixes.get('ExpressABPrefix', '')
        elif ab_type == 1:
            prefix = prefixes.get('GroundABPrefix', '')
        elif ab_type == 2:
            prefix = prefixes.get('MexicoABPrefix', '')

        if ab_type == 1 or ab_type == 0:
            temp = convert_base_10(air_bill_number, '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ')

        pad_len = max_len - len(prefix)

        while len(temp) < pad_len:
            temp = f"0{temp}"

        temp = f"{prefix}{temp}"

        return temp

    except _mssql.MssqlDatabaseException:
        return None
    finally:
        app_db.close_connection(conn)


def get_user_data(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        _client = service_manager.aws_cognito.client
        try:
            response = _client.get_user(
                AccessToken=request.headers['X-LSO-Authorization'].split(' ')[1],
            )
            user_attribute = response['UserAttributes']
            data = {}
            for attribute in user_attribute:
                try:
                    data[attribute['Name'].split(':')[1]] = attribute['Value']
                except IndexError:
                    data[attribute['Name']] = attribute['Value']
            request.data = data
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "TokenExpiredError", HTTPStatus.BAD_REQUEST)
        except KeyError:
            raise CustomError('Invalid Token', "InvalidTokenError")
        return fn(*args, **kwargs)

    return decorator


def send_html_email(RECIPIENT, customer_name, customer_address, customer_id, customer_email):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "LSO <notifications@lso.com>"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = Config.COGNITO_REGION

    # The subject line for the email.
    SUBJECT = "An new LSO account has been created"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("A new LSO account has been created with the following details\r\n"
                 f"Customer Name ${customer_name} "
                 f"Customer Address ${customer_address} "
                 f"Customer Id ${customer_id} "
                 f"Customer Email ${customer_email} "
                 )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head>
    <title></title>
    <meta name="viewport" content="width=device-width" />

    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@700&display=swap" rel="stylesheet">      
    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@600&display=swap" rel="stylesheet">
  </head>
    <body style="width: 100%; margin: auto; background-color: #F9F9FB;">
      <table 
          align="center" 
          border="0" 
          cellpadding="0" 
          cellspacing="0" 
          style="font-family: 'Atten New', sans-serif; margin: auto; background: #F9F9FB"
          width="100%" 
      >     
        <tr>
          <td align="center">
            <table 
                cellpadding="0" 
                cellspacing="0" 
                border="0" 
                align="center" 
                style="background: white;margin: 0 0;width: 512px;padding-top: 60px;position: relative;
                transform: translateY(40%);">
                <tr>
                  <td style="text-align: center;">
                    <img style="width:50%;" src="https://uploads-ssl.webflow.com/610bd2c21f6eaa53c3ceab9f/61334a409ce24a71f84b8c81_lso-logo.png"/>
                  </td>

                  </tr>      
                  <tr>
                    <td style="padding-bottom: 20px; padding-top: 20px;">
                      <h1 style="text-align: center; font-weight: 600; line-height: 28.13px; font-size: 18px;color: #061908;">A new LSO  account has been created with the below</h1>
                        <div style="margin: 0px 25px 0 25px; padding-top: 5px;">
                        <p style="font-weight: 400; font-size: 16px;line-height: 20px; text-align: left;"> <b>Customer Name: </b> {name},</p>
                        <p style="font-weight: 400; font-size: 16px;line-height: 20px; text-align: left;"><b>Customer Address:</b> {address},</p>
                        <p style="font-weight: 400; font-size: 16px;line-height: 20px; text-align: left;"><b>Customer ID:</b>  {id},</p>
                        <p style="font-weight: 400; font-size: 16px;line-height: 20px; text-align: left;"><b>Email Address:</b>  {email},</p>

                        </div>
                    </td>
                  </tr>                 
            </table>
          </td>
        </tr>
      </table>


    </body>

</html>
                """.format(name=customer_name, address=customer_address, id=customer_id, email=customer_email)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
        return response
    # Display an error if something goes wrong.
    except ClientError as e:
        pass


def initiate_auth(user_profile, password, config, client, keep, need_pwd_change=None):
    response = client.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': f"{user_profile.get('LoginName', '').strip().replace(' ', '')}{user_profile.get('CustID', '')}",
            'PASSWORD': password
        },
        ClientId=config.COGNITO_APP_CLIENT_ID,
    )
    if keep == "true":
        data = response['AuthenticationResult']
    else:
        data = response['AuthenticationResult']
        data.pop('RefreshToken')
    data['username'] = user_profile.get('UserEmail', '')
    data['cust_id'] = user_profile.get('CustID', '')

    if need_pwd_change:
        data['change_password_required'] = True
    return data


def create_event_payload(config, data, password, trigger):
    return {
        "triggerSource": trigger,
        "region": config.COGNITO_REGION,
        "userPoolId": config.COGNITO_USERPOOL_ID,
        "userName": f"{data.get('LoginName', '').strip().replace(' ', '')}{data.get('CustID', '')}",
        "callerContext": {
            "awsSdkVersion": "aws-sdk-unknown-unknown",
            "clientId": config.COGNITO_APP_CLIENT_ID
        },
        "request": {
            "password": password,
            "validationData": {
                "custom:first_name": str(data.get('UserFirstName', '')),
                "custom:last_name": str(data.get('UserLastName', '')),
                "custom:business_name": str(data.get('CompanyName', '')),
                "custom:contact_number": str(data.get('CompanyPhone', '')),
                "custom:address": str(data.get('CompanyAddress1', '')),
                "custom:address_2": str(data.get('CompanyAddress2', '')),
                "custom:postal_code": str(data.get('CompanyZip', '')),
                "custom:city": str(data.get('CompanyCity', '')),
                "custom:state": str(data.get('CompanyState', '')),
                "custom:account_number": str(data.get('CustID', '')),
                "custom:user_id": str(data.get('UID', '')),
                "custom:login_name": str(data.get('LoginName', '').strip()),
                "email": str(data.get('UserEmail', ''))
            },
        }
    }


def duplicate_account_creation_html_email(RECIPIENT):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "LSO <notifications@lso.com>"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = Config.COGNITO_REGION

    # The subject line for the email.
    SUBJECT = "LSO Account Updates"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (
        "Good news! We noticed you’ve tried to use this email address to create a new account, but you already have a valid account with us.\r\n"
        f" To access your dashboard, just click ${Config.APP_LINK} and sign in</p> "
    )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head>
    <title></title>
    <meta name="viewport" content="width=device-width" />

    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@700&display=swap" rel="stylesheet">      
    <link rel="preconnect" href="https://fonts.gstatic.com">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@600&display=swap" rel="stylesheet">
  </head>
    <body style="width: 100%; margin: auto; background-color: #F9F9FB;">
      <table 
          align="center" 
          border="0" 
          cellpadding="0" 
          cellspacing="0" 
          style="font-family: 'Atten New', sans-serif; margin: auto; background: #F9F9FB"
          width="100%" 
      >     
        <tr>
          <td align="center">
            <table 
                cellpadding="0" 
                cellspacing="0" 
                border="0" 
                align="center" 
                style="background: white;margin: 0 0;width: 512px;padding-top: 60px;position: relative;
                transform: translateY(40%);">
                <tr>
                  <td style="text-align: center;">
                    <img style="width:50%;" src="https://uploads-ssl.webflow.com/610bd2c21f6eaa53c3ceab9f/61334a409ce24a71f84b8c81_lso-logo.png"/>
                  </td>

                  </tr>      
                  <tr>
                    <td style="padding-bottom: 20px; padding-top: 20px;">
                      <h1 style="text-align: center; font-weight: 600; line-height: 28.13px; font-size: 18px;color: #061908;">Account creation request received</h1>
                        <div style="margin: 0px 25px 0 25px; padding-top: 5px;">
                        <p style="font-weight: 400; font-size: 16px;line-height: 20px; text-align: left;"> Good news! We noticed you’ve tried to use this email address to create a new account, but you already have a valid account with us. To access your dashboard, just click <a href="${app_link}">link</a> and sign in</p>
                        <div style="text-align: center;margin-top: 60px;">
                                <a href="{app_link}/reset-password" style="text-decoration: none;"><span style="border-radius: 2px ;font-family: 'Open Sans', sans-serif ;border: none; padding: 14px 32px; background: #061908; font-size: 14px; font-weight: 600; color: white;">Reset Password</span></a>
                                <hr style="margin-top: 60px; border: 2px solid black;"/>
                              </div>
                        </div>
                    </td>
                  </tr>                 
            </table>
          </td>
        </tr>
      </table>


    </body>

</html>
                """.format(app_link=Config.APP_LINK)

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
        return response
    # Display an error if something goes wrong.
    except ClientError as e:
        pass


def option_visible(ui_option, cust_id, user_id):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)

    try:
        get_option_visible_query = "SELECT wo.Active, cwo.Enabled, wo.DefaultOn FROM WebsiteOption wo LEFT JOIN " \
                                   f"CustomerWebsiteOption cwo ON cwo.WebsiteOptionID = wo.ID AND " \
                                   f"cwo.CustID='{cust_id}' AND (cwo.UID = '{user_id}' OR cwo.AllProfiles = 1) " \
                                   f"WHERE LOWER(wo.UIOption) = LOWER('{ui_option}')"
        app_db.execute_query(cursor, get_option_visible_query)

        get_option_visible = cursor.fetchall()[0]

        if get_option_visible['DefaultOn'] and get_option_visible['Enabled'] == 0:
            return False

        if get_option_visible['DefaultOn']:
            return True

        if get_option_visible['Active'] and get_option_visible['Enabled']:
            return True

        return False
    except Exception as e:
        return False
    finally:
        app_db.close_connection(cursor)


def check_user_profile(account_number):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)

    try:
        check_profile_query = f"SELECT CustId FROM CustomerProfile WHERE CustId='{account_number}'"
        app_db.execute_query(cursor, check_profile_query)
        check_profile = cursor.fetchall()[0]
        if check_profile:
            return True
        else:
            return False
    except Exception:
        return False
    finally:
        app_db.close_connection(conn)


def get_user_profile_data(username=None, account_number=None):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)
    try:
        user_profile_query = f"SELECT * FROM UserProfile up LEFT OUTER JOIN OPENQUERY(OPS, " \
                             f"'SELECT CustID, AcctStatus FROM Customer WHERE CustID=''{account_number}''')" \
                             f" c ON c.CustID = up.CustID WHERE up.Active <> 0 AND " \
                             f"UPPER(RTRIM(up.LoginName)) = '{username.upper()}' " \
                             f"AND up.CustID='{account_number}'"

        app_db.execute_query(cursor, user_profile_query)
        try:
            user_profile = cursor.fetchall()[0]
        except IndexError:
            user_profile = {}
        return user_profile
    except Exception:
        return {}
    finally:
        app_db.close_connection(conn)


async def generate_air_bill_html(label_size=None, soap_response=None, user_id=None, a=2):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)

    try:
        airbill_number = soap_response.get('air_bill_no', '')
        update_user3_query = f"UPDATE IPackage SET User3 = '{user_id}' WHERE AirbillNo='{airbill_number}'"
        await app_execute_async_query(update_user3_query, cursor)
        app_db.commit_connection(conn)

        airbill_data_query = f"EXEC dbo.sp_GetAirbillInfo '{airbill_number}', '{airbill_number}', '' "
        await app_execute_async_query(airbill_data_query, cursor)
        airbill_data = cursor.fetchall()
        airbill_data[0]['PrintedDate'] = datetime.datetime.strftime(datetime.datetime.now(), '%m/%d/%Y')
        airbill_data[0]['LabelSize'] = label_size
        airbill_number = airbill_data[0].get("AirbillNo", '')
        service_manager.aws_s3.s3.download_file('prd-lso-genbarcode-dl', f'{airbill_number}.svg',
                                                f'static/{airbill_number}.svg')

        html = render_template("stdlabel.html", data=airbill_data[0])
        response = Response(html, mimetype='text/html; charset=UTF-8')
        response.headers['Cache-Control'] = 'max-age=0'
        response.headers['Accept-Ranges'] = 'none'
        return response.get_data(as_text=True)
    except Exception:
        try:
            return await generate_html_in_exception(label_size, soap_response, user_id)
        except Exception:
            return "<div></div>"
    finally:
        app_db.close_connection(conn)


async def generate_html_in_exception(label_size, soap_response, user_id):
    return await generate_air_bill_html(label_size, soap_response, user_id, 1)


async def register_package_notification(air_bill_number=None, email=None, n_type=None):
    conn = ops_db.create_connection()
    cursor = ops_db.create_cursor(conn)

    try:
        register_email_notification_query = "EXEC sp_RegisterEmailNotificationForPackage " \
                                            f"@AirbillNo='{air_bill_number}', @Email='{email}', " \
                                            f"@NotificationGroup='{n_type}', @ReferenceNo='null'"
        await ops_execute_async_query(register_email_notification_query, cursor)
        ops_db.commit_connection(conn)
    except Exception as e:
        pass
    finally:
        ops_db.close_connection(conn)


async def app_execute_async_query(query, cursor):
    await app_db.execute_query_async(cursor, query)


async def ops_execute_async_query(query, cursor):
    await ops_db.execute_query_async(cursor, query)


async def app_execute_async_query(query, cursor):
    await app_db.execute_query_async(cursor, query)


async def ops_execute_async_query(query, cursor):
    await ops_db.execute_query_async(cursor, query)


def get_soap_text(elem, attribute):
    try:
        return elem.find(attribute).get_text()
    except AttributeError:
        return ''
