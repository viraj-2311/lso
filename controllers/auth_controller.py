import json
from datetime import datetime
from http import HTTPStatus

from botocore.exceptions import ParamValidationError
from flask import request
from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from config import Config
from main import service_manager, app_db
from services.soap_requests.account_service import create_account
from utilities import custom_response, strip_specials, validate_email, validate_phone, validate_zip, \
    get_user_data, initiate_auth, create_event_payload, send_html_email, duplicate_account_creation_html_email, \
    option_visible, get_user_profile_data, check_user_profile

from services.payfabric_service import create_and_process_transaction, create_credit_card

auth_ns = Namespace("/auth", description="auth related operations")

_client = service_manager.aws_cognito.client
_lambda_client = service_manager.aws_lambda.aws_lambda


@auth_ns.route("/signup")
class Signup(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        requester_first_name = payload.get("requester_first_name", None)
        requester_last_name = payload.get("requester_last_name", None)
        requester_phone = payload.get("requester_phone", None)
        requester_email = payload.get("requester_email", None)
        company_name = payload.get("company_name", None)
        company_phone = payload.get("company_phone", None)
        company_phy_address_1 = payload.get("company_phy_address_1", None)
        company_phy_address_2 = payload.get("company_phy_address_2", None)
        company_phy_address_3 = payload.get("company_phy_address_3", None)
        company_phy_city = payload.get("company_phy_city", None)
        company_phy_state = payload.get("company_phy_state", None)
        company_phy_zip = payload.get("company_phy_zip", None)
        company_bill_address_1 = payload.get("company_bill_address_1", None)
        company_bill_address_2 = payload.get("company_bill_address_2", None)
        company_bill_city = payload.get("company_bill_city", None)
        company_bill_state = payload.get("company_bill_state", None)
        company_bill_zip = payload.get("company_bill_zip", None)
        how_hear_about = payload.get("how_hear_about", 0)
        login_name = payload.get("login_name", None)
        user_pwd = payload.get("user_pwd", None)
        comments = payload.get("comments", None)
        cc_first_name = payload.get('cc_first_name', '')
        cc_last_name = payload.get('cc_last_name', '')
        cc_name = f"{cc_first_name} {cc_last_name}"
        cc_number = payload.get("cc_number", 0)
        cc_type = payload.get("cc_type", '')
        cc_exp_month = payload.get("cc_exp_month", 0)
        cc_exp_year = payload.get("cc_exp_year", 0)
        verification_code = payload.get("verification_code", 0)
        billing_zip = payload.get("billing_zip", None)
        cc_opt_out = payload.get("cc_opt_out", 'false')
        campaign_name = payload.get("campaign_name", None)
        campaign_source_code = payload.get("campaign_source_code", None)
        referral_code = payload.get("referral_code", None)
        type_of_business = payload.get("type_of_business", None)
        country = payload.get("country", None)
        packages_per_day = payload.get("packages_per_day", None)

        json_dic = dict()
        json_dic['Card'] = {}
        json_dic['Card']['Billto'] = {}
        json_dic['Card']['CardHolder'] = {}

        json_dic['Amount'] = 1
        json_dic["Card"]['Customer'] = "01000"
        json_dic["Card"]['CardName'] = cc_type
        json_dic["Card"]['IsDefaultCard'] = "false"
        json_dic["Card"]['Account'] = cc_number
        json_dic["Card"]['ExpDate'] = f"{cc_exp_month}{cc_exp_year}"
        json_dic["Card"]['Phone'] = requester_phone
        json_dic["Card"]['Email'] = requester_email
        json_dic["Card"]['Billto']['Country'] = country
        json_dic["Card"]['Billto']['Line1'] = company_bill_address_1
        json_dic["Card"]['Billto']['Zip'] = billing_zip
        json_dic["Card"]['CardHolder']['FirstName'] = cc_first_name
        json_dic["Card"]['CardHolder']['LastName'] = cc_last_name
        json_dic["Currency"] = 'USD'
        json_dic["Customer"] = "01000"
        json_dic["Type"] = "Book"
        json_dic["SetupId"] = "EVO"

        transaction_details_json = create_and_process_transaction(json_dic)
        if transaction_details_json["Status"] == "Approved":

            create_account_info = create_account(requester_first_name=requester_first_name,
                                                 requester_last_name=requester_last_name,
                                                 requester_phone=requester_phone,
                                                 requester_email=requester_email, company_name=company_name,
                                                 company_phone=company_phone,
                                                 company_phy_address_1=company_phy_address_1,
                                                 company_phy_address_2=company_phy_address_2,
                                                 company_phy_city=company_phy_city, company_phy_state=company_phy_state,
                                                 company_phy_zip=company_phy_zip,
                                                 company_bill_address_1=company_bill_address_1,
                                                 company_bill_address_2=company_bill_address_2,
                                                 company_bill_city=company_bill_city,
                                                 company_bill_state=company_bill_state,
                                                 company_bill_zip=company_bill_zip, how_hear_about=0,
                                                 login_name=login_name, user_pwd=user_pwd, comments=comments,
                                                 cc_name=cc_name, cc_number=cc_number, cc_type=cc_type,
                                                 cc_exp_month=cc_exp_month, cc_exp_year=cc_exp_year,
                                                 verification_code=verification_code, billing_zip=billing_zip,
                                                 cc_opt_out=cc_opt_out, campaign_name=campaign_name,
                                                 campaign_source_code=campaign_source_code, referral_code=referral_code,
                                                 number_package_per_day=packages_per_day,
                                                 business_type=type_of_business, new_how_hear_about=how_hear_about)
            conn = app_db.create_connection()
            cursor = app_db.create_cursor(conn)
            try:
                if create_account_info[1] == "success":
                    get_user_data_query = f"SELECT * FROM UserProfile WHERE " \
                                          f"CustID='{create_account_info[0].get('customer_id')}'"
                    app_db.execute_query(cursor, get_user_data_query)
                    get_user_data = cursor.fetchall()[0]

                    if get_user_data:
                        response = _client.sign_up(
                            ClientId=Config.COGNITO_APP_CLIENT_ID,
                            Username=f"{get_user_data.get('LoginName', '').strip().replace(' ', '')}{get_user_data.get('CustID', '')}",
                            Password=user_pwd,
                            UserAttributes=[
                                {
                                    'Name': 'email',
                                    'Value': get_user_data.get('UserEmail', '')
                                },
                                {
                                    'Name': 'custom:first_name',
                                    'Value': requester_first_name
                                },
                                {
                                    'Name': 'custom:last_name',
                                    'Value': requester_last_name
                                },
                                {
                                    'Name': 'custom:business_name',
                                    'Value': company_name
                                },
                                {
                                    'Name': 'custom:contact_number',
                                    'Value': company_phone
                                },
                                {
                                    'Name': 'custom:type_of_business',
                                    'Value': type_of_business
                                },
                                {
                                    'Name': 'custom:country',
                                    'Value': country
                                },
                                {
                                    'Name': 'custom:address',
                                    'Value': company_phy_address_1
                                },
                                {
                                    'Name': 'custom:address_2',
                                    'Value': company_phy_address_2
                                },
                                {
                                    'Name': 'custom:address_3',
                                    'Value': company_phy_address_3
                                },
                                {
                                    'Name': 'custom:postal_code',
                                    'Value': company_phy_zip
                                },
                                {
                                    'Name': 'custom:city',
                                    'Value': company_phy_city
                                },
                                {
                                    'Name': 'custom:state',
                                    'Value': company_phy_state
                                },
                                {
                                    'Name': 'custom:packages_per_day',
                                    'Value': packages_per_day
                                },
                                {
                                    'Name': 'custom:account_number',
                                    'Value': create_account_info[0].get('customer_id')
                                },
                                {
                                    'Name': 'custom:user_id',
                                    'Value': f"{get_user_data.get('UID')}"
                                },
                                {
                                    'Name': 'custom:login_name',
                                    'Value': f"{get_user_data.get('LoginName')}"
                                },
                            ],
                        )

                        card = dict()
                        card['Billto'] = {}
                        card['CardHolder'] = {}
                        card['Account'] = cc_number
                        card['Customer'] = create_account_info[0].get("customer_id")
                        card['IsDefaultCard'] = 'false'
                        card['Tender'] = 'CreditCard'
                        card['ExpDate'] = f"{cc_exp_month}{cc_exp_year}"
                        card['Billto']['Line1'] = company_bill_address_1
                        card['Billto']['Phone'] = requester_phone
                        card['Billto']['Zip'] = billing_zip
                        card['Billto']['Email'] = requester_email
                        card['CardHolder']['FirstName'] = cc_first_name
                        card['CardHolder']['LastName'] = cc_last_name

                        card_response = create_credit_card(card)
                        # Send an email to the billing team for succesful account creation. replace fanyuiharisu@gmail.com with the billing@lso.com address
                        send_html_email(Config.BILLING_EMAIL, requester_first_name, company_phy_address_1,
                                        create_account_info[0].get('customer_id'), requester_email)

                        return custom_response("success", "Successfully Sign up.", HTTPStatus.OK,
                                               data=create_account_info[0])
                elif create_account_info[1] == "error":
                    return custom_response("error", create_account_info[0], HTTPStatus.BAD_REQUEST)
                else:
                    return custom_response("error", "An unexpected error occurred, Please try again.",
                                           HTTPStatus.BAD_REQUEST)
            except _client.exceptions.UsernameExistsException:
                duplicate_account_creation_html_email(requester_email)
                return custom_response("success", "Check your email for further details.", HTTPStatus.OK)
            except _client.exceptions.InvalidParameterException:
                return custom_response("error", "Invalid parameters.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.InvalidPasswordException:
                return custom_response("error", "Invalid password.", HTTPStatus.BAD_REQUEST)
            except Exception as e:
                return custom_response("error", "An unexpected error occurred. Please try again..",
                                       HTTPStatus.BAD_REQUEST)
        else:
            return custom_response("error",
                                   f"{transaction_details_json['Status']} {transaction_details_json['Message']}",
                                   HTTPStatus.BAD_REQUEST)


@auth_ns.route("/signin")
class Signin(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        customer_id = strip_specials(payload.get('customer_id', ''))
        username = strip_specials(payload.get('username', ''))
        password = strip_specials(payload.get('password', ''))
        keep = strip_specials(payload.get('keep', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)
        try:
            login_attempt_query = "EXEC sp_SummStatsInc 'LOGINATTEMPTS'"
            app_db.execute_query(cursor, login_attempt_query)
            app_db.commit_connection(conn)

            if not customer_id:
                return custom_response("error", "Invalid User Credentials, Please try again.", HTTPStatus.BAD_REQUEST)
            elif not username:
                login_failed_uid_query = "sp_SummStatsInc 'LOGINFAILEDUID'"
                app_db.execute_query(cursor, login_failed_uid_query)
                app_db.commit_connection(conn)

                return custom_response("error", "Invalid User Credentials, Please try again.", HTTPStatus.BAD_REQUEST)
            elif not password:
                login_failed_pwd_query = "exec sp_SummStatsInc 'LOGINFAILEDPWD'"
                app_db.execute_query(cursor, login_failed_pwd_query)
                app_db.commit_connection(cursor)

                return custom_response("error", "Invalid User Credentials.", HTTPStatus.BAD_REQUEST)
            else:
                check_user_profile = get_user_profile_data(username=username, account_number=customer_id)
                if not check_user_profile:
                    login_failed_uid_query = "sp_SummStatsInc 'LOGINFAILEDUID'"
                    app_db.execute_query(cursor, login_failed_uid_query)
                    app_db.commit_connection(conn)
                    return custom_response("error", "The user is not Active. Please contact Customer Service at "
                                                    "(800) 800-8984.",
                                           HTTPStatus.BAD_REQUEST)

                if check_user_profile.get('AccountLockout', ''):
                    account_locked_query = "EXEC sp_SummStatsInc 'ACCOUNTLOCKED'"
                    app_db.execute_query(cursor, account_locked_query)

                    return custom_response("error",
                                           "Your Account has been locked out. Please contact Customer Service at "
                                           "(800) 800-8984.", HTTPStatus.BAD_REQUEST)

                if check_user_profile.get('AcctStatus', '') != 'A' and check_user_profile.get('AcctStatus', '') != 'R':
                    return custom_response("error",
                                           "Please contact Customer Service at (800) 800-8984 to check the status"
                                           " of your account.", HTTPStatus.BAD_REQUEST)

                user_id = check_user_profile.get('UID', '')
                user_password = strip_specials(check_user_profile.get('UserPWD', ''))
                login_attempts_today = check_user_profile.get('LoginAttemptsToday', '')
                login_failed_today = check_user_profile.get('LoginFailedToday', '')
                logins_to_date = check_user_profile.get('LoginsToDate', '')
                user_email = check_user_profile.get('UserEmail', '')

                check_max_failures_query = "SELECT FailureRetry FROM WebControl"
                app_db.execute_query(cursor, check_max_failures_query)
                check_max_failures = cursor.fetchall()[0]

                if check_max_failures:
                    failure_retry = check_max_failures['FailureRetry']
                else:
                    failure_retry = 5

                if login_failed_today >= failure_retry:
                    login_failed_today += 1
                    login_attempts_today += 1

                    login_failed_uid_query = "sp_SummStatsInc 'LOGINFAILEDUID'"
                    app_db.execute_query(cursor, login_failed_uid_query)
                    app_db.commit_connection(conn)

                    add_failure_query = f"UPDATE UserProfile SET LoginAttemptsToday = '{login_attempts_today}', " \
                                        f"LoginFailedToday = '{login_failed_today}' WHERE UID = '{user_id}'"

                    app_db.execute_query(cursor, add_failure_query)
                    app_db.commit_connection(conn)

                    return custom_response("error", "Max login failed today", HTTPStatus.BAD_REQUEST)

                elif password == user_password:
                    login_attempts_today += 1
                    logins_to_date += 1

                    add_success_query = f"UPDATE UserProfile SET LoginAttemptsToday = '{login_attempts_today}', " \
                                        f"LoginsToDate = '{logins_to_date}', " \
                                        f"LastLoginDate = '{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}' WHERE " \
                                        f"UID = '{user_id}'"

                    app_db.execute_query(cursor, add_success_query)
                    app_db.commit_connection(conn)

                    try:
                        get_user_response = _client.admin_get_user(UserPoolId=Config.COGNITO_USERPOOL_ID,
                                                                   Username=f"{check_user_profile.get('LoginName', '').strip().replace(' ', '')}{check_user_profile.get('CustID', '')}")

                        if get_user_response:
                            data = initiate_auth(user_profile=check_user_profile, password=password,
                                                 config=Config, client=_client, keep=keep)
                            return custom_response("success", "Sign in", HTTPStatus.OK, data)
                    except _client.exceptions.UserNotFoundException:
                        event_payload = create_event_payload(config=Config, data=check_user_profile, password=password,
                                                             trigger='UserMigration_Authentication')
                        response = _lambda_client.invoke(
                            FunctionName='MigrateUserLive',
                            InvocationType='RequestResponse',
                            LogType='None',
                            Payload=json.dumps(event_payload)
                        )
                        response_payload = str(response['Payload'].read())
                        if "UserCreatedCognito" in response_payload:
                            data = initiate_auth(user_profile=check_user_profile, password='Dummy@1234',
                                                 config=Config, client=_client, keep=keep, need_pwd_change=True)
                            return custom_response("success", "Sign in", HTTPStatus.OK, data)

                    except _client.exceptions.NotAuthorizedException:
                        data = initiate_auth(user_profile=check_user_profile, password='Dummy@1234',
                                             config=Config, client=_client, keep=keep, need_pwd_change=True)
                        return custom_response("success", "Sign in", HTTPStatus.OK, data)
                elif password != user_password:
                    login_failed_today += 1
                    login_attempts_today += 1

                    login_failed_pwd_query = "exec sp_SummStatsInc 'LOGINFAILEDPWD'"
                    app_db.execute_query(cursor, login_failed_pwd_query)
                    app_db.commit_connection(conn)

                    add_failure_query = f"UPDATE UserProfile SET LoginAttemptsToday = '{login_attempts_today}', " \
                                        f"LoginFailedToday = '{login_failed_today}' WHERE UID = '{user_id}'"

                    app_db.execute_query(cursor, add_failure_query)
                    app_db.commit_connection(conn)

                    return custom_response("error", "Invalid User Credentials, Please try again.",
                                           HTTPStatus.UNAUTHORIZED)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except _client.exceptions.InvalidParameterException as e:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", {
                "error": "User not confirmed",
                "email": user_email,
                "code": "USER_NOT_CONFIRMED",
            }, HTTPStatus.NOT_FOUND)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Invalid User Credentials, Please try again", HTTPStatus.UNAUTHORIZED)
        except Exception as e:
            return custom_response("error", "Invalid User Credentials, Please try again", HTTPStatus.UNAUTHORIZED)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/change_password")
class ChangePassword(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        user_data = request.data
        account_number = user_data.get('account_number', '')

        if not account_number:
            return custom_response("error", "Invalid User Credentials.", HTTPStatus.UNAUTHORIZED)
        if not (account_number.isnumeric()):
            return custom_response("error", "Invalid User Credentials.", HTTPStatus.UNAUTHORIZED)

        username = strip_specials(payload.get('username', '')).upper()
        old_password = payload.get('old_password', '')
        new_password = payload.get('new_password', '')

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)
        try:
            password_check_query = f"SELECT UserPWD FROM UserProfile WHERE CustId = '{account_number}' " \
                                   f"AND UPPER(LoginName) = '{username}'"

            app_db.execute_query(cursor, password_check_query)

            try:
                password_check = cursor.fetchall()[0]
            except IndexError:
                password_check = {}

            if password_check:
                db_password = strip_specials(password_check.get('UserPWD', ''))
            else:
                return custom_response("error", "Invalid User Credentials.", HTTPStatus.UNAUTHORIZED)

            if old_password != db_password:
                return custom_response("error", "Invalid User Credentials.", HTTPStatus.UNAUTHORIZED)
            elif old_password == db_password:
                if new_password == old_password:
                    return custom_response("error", "New password must be different from current password. "
                                                    "Please try again.", HTTPStatus.BAD_REQUEST)
                else:
                    response = _client.change_password(
                        PreviousPassword=old_password,
                        ProposedPassword=new_password,
                        AccessToken=request.headers['X-LSO-Authorization'].split(' ')[1]
                    )

                    password_change_query = f"UPDATE UserProfile SET UserPWD = '{new_password}', PWDResentCount = '0', " \
                                            f"PWDChangedLast = getdate() WHERE CustId = {account_number} AND " \
                                            f"UPPER(LoginName)='{username}'"
                    app_db.execute_query(cursor, password_change_query)
                    app_db.commit_connection(conn)

                    return custom_response("success", "Password successfully changed.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.InvalidPasswordException:
            return custom_response("error", "Invalid password.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
        except _client.exceptions.LimitExceededException:
            return custom_response("error", "Limit exceeded.", HTTPStatus.TOO_MANY_REQUESTS)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except ParamValidationError:
            return custom_response("error", "New password must contain upper, lower, and digit and 8 characters long",
                                   HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/forgot_password")
class ForgotPassword(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        customer_id = strip_specials(payload.get('customer_id', ''))
        username = strip_specials(payload.get('username', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        if not customer_id.isnumeric():
            return custom_response("error", "Invalid User Credentials.",
                                   HTTPStatus.BAD_REQUEST)

        email_check_query = f"SELECT * FROM UserProfile WHERE " \
                            f"UPPER(RTRIM(LoginName))='{username.upper()}' AND CustID='{customer_id}'"
        app_db.execute_query(cursor, email_check_query)
        try:
            email_check = cursor.fetchall()[0]
        except IndexError:
            email_check = None

        if not email_check:
            return custom_response("error", "Invalid User Credentials.",
                                   HTTPStatus.UNAUTHORIZED)
        else:
            user_id = email_check.get('UID', '')
            email = email_check.get('UserEmail', '')
            pass_resent_count = email_check.get('PWDResentCount', '')
        if email:
            try:

                event_payload = create_event_payload(config=Config, data=email_check,
                                                     password=email_check.get('UserPWD', ''),
                                                     trigger='UserMigration_ForgotPassword')
                response = _lambda_client.invoke(
                    FunctionName='MigrateUserLive',
                    InvocationType='RequestResponse',
                    LogType='None',
                    Payload=json.dumps(event_payload)
                )
                response_payload = str(response['Payload'].read())
                if "NoEmail" in response_payload:
                    return custom_response("error",
                                           "Please contact Customer Service at (800) 800-8984 and add email id to your account.",
                                           HTTPStatus.BAD_REQUEST)
                elif "NotValidEmail" in response_payload:
                    return custom_response("error",
                                           "You do not have valid email address to your account, Please contact Customer Service at (800) 800-8984 and update the email.",
                                           HTTPStatus.BAD_REQUEST)
                elif "LinkSentCognito" in response_payload:

                    password_sent_query = f"UPDATE UserProfile SET PWDResentLast=" \
                                          f"'{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}', " \
                                          f"PWDResentCount='{pass_resent_count + 1}', PWDResentToday=PWDResentToday+1 " \
                                          f"WHERE UID='{user_id}'"
                    app_db.execute_query(cursor, password_sent_query)
                    app_db.commit_connection(conn)

                    return custom_response("success", "Code sent.", HTTPStatus.OK,
                                           data={'email': email_check.get('UserEmail', '')})
                elif "UserCreatedCognito" in response_payload:
                    response = _client.forgot_password(
                        ClientId=Config.COGNITO_APP_CLIENT_ID,
                        Username=f"{email_check.get('LoginName', '').strip().replace(' ', '')}{email_check.get('CustID', '')}",
                    )
                    password_sent_query = f"UPDATE UserProfile SET PWDResentLast=" \
                                          f"'{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}', " \
                                          f"PWDResentCount='{pass_resent_count + 1}', PWDResentToday=PWDResentToday+1 " \
                                          f"WHERE UID='{user_id}'"
                    app_db.execute_query(cursor, password_sent_query)
                    app_db.commit_connection(conn)
                    return custom_response("success", "Code sent.", HTTPStatus.OK,
                                           data={'email': email_check.get('UserEmail', '')})
            except _mssql.MssqlDatabaseException:
                return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
            except _client.exceptions.InvalidParameterException:
                return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.NotAuthorizedException:
                return custom_response("error", "Not authorized.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.CodeDeliveryFailureException:
                return custom_response("error", "Code was not delivered.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.LimitExceededException:
                return custom_response("error", "Limit exceeded.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.UserNotFoundException:
                return custom_response("error", "User not found.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.UserNotConfirmedException:
                return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
            except Exception as e:
                return custom_response("error", "Something bad happened.", HTTPStatus.BAD_REQUEST)
            finally:
                app_db.close_connection(conn)
        else:
            return custom_response("error", "Email is not present.", HTTPStatus.BAD_REQUEST)


@auth_ns.route("/confirm_forgot_password")
class ConfirmForgotPassword(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        username = payload.get('username', '')
        confirmation_code = payload.get('confirmation_code', '')
        password = payload.get('password', '')
        confirm_password = payload.get('confirm_password', '')
        user_id = payload.get('user_id', '')

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if password == confirm_password:
                response = _client.confirm_forgot_password(
                    ClientId=Config.COGNITO_APP_CLIENT_ID,
                    Username=username,
                    ConfirmationCode=confirmation_code,
                    Password=password
                )

                update_password_query = f"UPDATE UserProfile SET UserPWD='{password}', " \
                                        f"PWDResentLast='{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}'" \
                                        f"WHERE UID='{user_id}'"

                app_db.execute_query(cursor, update_password_query)
                app_db.commit_connection(conn)
                return custom_response("success", "Password changed.", HTTPStatus.OK)
            else:
                return custom_response("error", "Password did not match.", HTTPStatus.FORBIDDEN)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.InvalidPasswordException:
            return custom_response("error", "Invalid password.", HTTPStatus.FORBIDDEN)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
        except _client.exceptions.CodeMismatchException:
            return custom_response("error", "Invalid code.", HTTPStatus.FORBIDDEN)
        except _client.exceptions.ExpiredCodeException:
            return custom_response("error", "Code expired.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.TooManyFailedAttemptsException:
            return custom_response("error", "Too many failed attempts.", HTTPStatus.TOO_MANY_REQUESTS)
        except _client.exceptions.LimitExceededException:
            return custom_response("error", "Limit exceeded.", HTTPStatus.TOO_MANY_REQUESTS)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route('/update_profile')
class UpdateProfile(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        old_email = payload.get('old_email', '')
        new_email = payload.get('new_email', '')

        user_data = request.data

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if not new_email:
                return custom_response("error", "Please enter new email.", HTTPStatus.BAD_REQUEST)

            get_email_query = "SELECT ISNULL(UserEmail, '') AS UserEmail FROM UserProfile WHERE " \
                              f"UID='{user_data.get('user_id')}'"
            app_db.execute_query(cursor, get_email_query)

            get_email = cursor.fetchall()[0]
            if get_email:
                if get_email.get('UserEmail').strip() != old_email:
                    return custom_response("error", "Old email is not match.", HTTPStatus.BAD_REQUEST)

            if not validate_email(new_email):
                return custom_response("error", "Please enter a valid email.", HTTPStatus.BAD_REQUEST)

            if old_email == new_email:
                return custom_response("error", "New email and old email are same", HTTPStatus.BAD_REQUEST)
            else:
                response = _client.admin_update_user_attributes(
                    UserPoolId=Config.COGNITO_USERPOOL_ID,
                    Username=f"{user_data.get('login_name').strip().replace(' ', '')}{user_data.get('account_number')}",
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': new_email
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        },
                    ]
                )
                update_email_query = f"UPDATE UserProfile SET USerEmail='{new_email}' " \
                                     f"WHERE UID='{user_data.get('user_id')}'"
                app_db.execute_query(cursor, update_email_query)
                app_db.commit_connection(conn)
                return custom_response("success", "Attribute updated.", HTTPStatus.OK)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
        except _client.exceptions.CodeDeliveryFailureException:
            return custom_response("error", "Code was not delivered.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.UNAUTHORIZED)
        except _client.exceptions.AliasExistsException:
            return custom_response("error", "New email are already in use", HTTPStatus.UNAUTHORIZED)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/get_refresh_token")
class GetRefreshToken(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        refresh_token = payload.get('refresh_token', '')
        try:
            response = _client.initiate_auth(
                AuthFlow='REFRESH_TOKEN_AUTH',
                ClientId=Config.COGNITO_APP_CLIENT_ID,
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                },
            )
            data = response['AuthenticationResult']
            return custom_response("success", "Tokens.", HTTPStatus.OK, data)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Username or Password are incorrect.", HTTPStatus.UNAUTHORIZED)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)


@auth_ns.route("/get_account")
class GetAccount(Resource):
    @cognito_auth_required
    def get(self):
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

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

            data['use_simple_pricing'] = False

            account_number = data.get("account_number")
            if account_number == "156759" or account_number == "155168" or account_number == "67588" \
                    or account_number == "1" or account_number == "94140" or account_number == "126775" \
                    or account_number == "154484" or account_number == "155112":
                data['use_simple_pricing'] = True
                if account_number == "156759":
                    data['def_signature_requirement'] = "G"
                elif account_number == "67588":
                    data['def_signature_requirement'] = "A"

            if option_visible("HCGeneralSig", data.get("account_number"), data.get("user_id")):
                data["def_signature_requirement"] = "G"

            if option_visible("HCAdultSig", data.get("account_number"), data.get("user_id")):
                data["def_signature_requirement"] = "A"

            if option_visible("ForceSimple", account_number, data.get("user_id")):
                data['use_simple_pricing'] = True

            get_customer_query = "SELECT * FROM OPENQUERY(OPS, 'SELECT CustId, DisallowSimplePricing " \
                                 f"FROM Customer WHERE CustId=''{data.get('account_number')}''')"
            app_db.execute_query(cursor, get_customer_query)

            get_customer = cursor.fetchall()[0]

            if get_customer:
                data["disallow_simple_pricing"] = get_customer.get('DisallowSimplePricing')
            else:
                data["disallow_simple_pricing"] = False

            user_profile = get_user_profile_data(username=data.get("login_name"),
                                                 account_number=data.get('account_number'))
            if user_profile.get("UseLocBillingRef"):
                data['use_saved_billing_ref'] = True
            else:
                data['use_saved_billing_ref'] = False

            data['hard_code_billing_ref'] = user_profile.get('HardCodeBillingRef', '')
            data['hard_coded_billing_ref_value'] = user_profile.get('HardCodedBillingRefValue', '')
            data['hard_code_billing_ref_2'] = user_profile.get('HardCodeBillingRef2', '')
            data['hard_coded_billing_ref_value_2'] = user_profile.get('HardCodedBillingRefValue2', '')

            data['billing_ref_required'] = user_profile.get('BillingRefRequired', '')
            data['email_delivery_notification'] = user_profile.get('EmailPOD', '')
            data['print_published_rates'] = user_profile.get('PrintPublishedRates', '')
            data['print_to_label'] = user_profile.get('PrintToLabel', '')
            data['default_service'] = user_profile.get('DefaultService', '')
            data['address'] = user_profile.get('CompanyAddress1', '')

            try:
                response = _client.initiate_auth(
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters={
                        'USERNAME': f"{data.get('login_name', '').strip().replace(' ', '')}{data.get('account_number', '')}",
                        'PASSWORD': 'Dummy@1234'
                    },
                    ClientId=Config.COGNITO_APP_CLIENT_ID,
                )
                data['change_password_required'] = True
            except _client.exceptions.NotAuthorizedException:
                pass

            return custom_response("success", "Account information.", HTTPStatus.OK, data)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route('/customer_add_user')
class AddUserSignup(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        account_number = strip_specials(payload.get('account_number', '')).strip()
        username = strip_specials(payload.get('username', '')).strip()
        first_name = strip_specials(payload.get('first_name', '')).strip()
        last_name = strip_specials(payload.get('last_name', '')).strip()
        password = strip_specials(payload.get('password', '')).strip()
        confirm_password = strip_specials(payload.get('confirm_password', '')).strip()
        email = strip_specials(payload.get('email', '')).strip()
        company_name = strip_specials(payload.get('company_name', '')).strip()
        company_phone = strip_specials(payload.get('company_phone', '')).strip()
        company_address = strip_specials(payload.get('company_address', '')).strip()
        company_address_2 = strip_specials(payload.get('company_address_2', '')).strip()
        company_city = strip_specials(payload.get('company_city', '')).strip()
        company_state = strip_specials(payload.get('company_state', '')).strip()
        company_zip_code = strip_specials(payload.get('company_zip_code', '')).strip()
        billing_reference_required = "0" if strip_specials(
            payload.get('billing_reference_required')).strip() != "1" else "1"
        is_user_admin = "0" if strip_specials(payload.get('is_user_admin', '')).strip() != "1" else "1"
        show_only_user_shipments = "0" if strip_specials(
            payload.get('show_only_user_shipments', '')).strip() != "1" else "1"
        disable_billing_reference_required = "0" if strip_specials(
            payload.get('disable_billing_reference_required', '')).strip() != "1" else "1"
        active = "0" if strip_specials(payload.get('active', '')).strip() != "1" else "1"

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:
            if not username:
                return custom_response("error", "Login name must not be blank.", HTTPStatus.BAD_REQUEST)
            else:
                get_user_profile_query = f"SELECT UID FROM UserProfile WHERE CustID='{account_number}' " \
                                         f"AND UPPER(LoginName)='{username.upper()}'"
                app_db.execute_query(cursor, get_user_profile_query)
                get_user_profile = cursor.fetchall()
                if get_user_profile:
                    return custom_response("error", "User name already exists. Please select another name.",
                                           HTTPStatus.BAD_REQUEST)
                else:
                    if not validate_email(email):
                        return custom_response("error", "Invalid email address.", HTTPStatus.BAD_REQUEST)
                    elif not first_name:
                        return custom_response("error", "First Name must not be blank.", HTTPStatus.BAD_REQUEST)
                    elif not last_name:
                        return custom_response("error", "Last Name must not be blank.", HTTPStatus.BAD_REQUEST)
                    elif not password or not confirm_password:
                        return custom_response("error", "Password must not be blank.", HTTPStatus.BAD_REQUEST)
                    elif password != confirm_password:
                        return custom_response("error", "New Password and Confirmation don't match. Please try again.",
                                               HTTPStatus.BAD_REQUEST)
                    elif not validate_phone(company_phone):
                        return custom_response("error", "Company phone empty or invalid.", HTTPStatus.BAD_REQUEST)
                    elif not company_address:
                        return custom_response("error", "Company Address must not be blank.", HTTPStatus.BAD_REQUEST)
                    elif not company_city:
                        return custom_response("error", "Company City must not be blank.", HTTPStatus.BAD_REQUEST)
                    elif len(company_state) != 2:
                        return custom_response("error", "Company State invalid.", HTTPStatus.BAD_REQUEST)
                    elif not validate_zip(company_zip_code):
                        return custom_response("error", "Invalid Company Zip.", HTTPStatus.BAD_REQUEST)
                    else:
                        uid_query = f"EXEC sp_getuid ''"
                        app_db.execute_query(cursor, uid_query)
                        app_db.commit_connection(conn)

                        get_uid_query = f"SELECT LastUIDAssigned FROM WebControl WHERE ControlNo='LSO'"
                        app_db.execute_query(cursor, get_uid_query)
                        uid = cursor.fetchall()[0]['LastUIDAssigned']

                        add_user_profile_query = f"INSERT INTO UserProfile (UID, CustID, LoginName, UserFirstName, " \
                                                 f"UserLastName, UserPWD, UserEmail, CompanyName, CompanyPhone, " \
                                                 f"CompanyAddress1, CompanyAddress2, CompanyCity, CompanyState, " \
                                                 f"CompanyZip, BillingRefRequired, IsUserAdmin, ShowOnlyUserShipments" \
                                                 f", DisableBillingReferenceRequired, Active, CreatedBy, CreateDate" \
                                                 f", Administrator) VALUES ({uid}, {account_number}, '{username}'," \
                                                 f" '{first_name}', '{last_name}', '{password}', '{email}'," \
                                                 f" '{company_name}', '{company_phone}', '{company_address}'," \
                                                 f" '{company_address_2}', '{company_city}', '{company_state}'," \
                                                 f" '{company_zip_code}', '{billing_reference_required}'," \
                                                 f" '{is_user_admin}', '{show_only_user_shipments}'," \
                                                 f" '{disable_billing_reference_required}', '{active}'," \
                                                 f" '{user_data.get('user_id', '')}', " \
                                                 f"'{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}', '0')"
                        app_db.execute_query(cursor, add_user_profile_query)
                        app_db.commit_connection(conn)

                        get_user_data_query = f"SELECT * FROM UserProfile WHERE " \
                                              f"UID='{uid}'"
                        app_db.execute_query(cursor, get_user_data_query)
                        get_user_data = cursor.fetchall()[0]

                        create_user_response = _client.admin_create_user(
                            UserPoolId=Config.COGNITO_USERPOOL_ID,
                            Username=f"{get_user_data.get('LoginName', '').strip().replace(' ', '')}{get_user_data.get('CustID', '')}",
                            UserAttributes=[
                                {
                                    'Name': 'email',
                                    'Value': email
                                },
                                {
                                    'Name': 'custom:first_name',
                                    'Value': first_name
                                },
                                {
                                    'Name': 'custom:last_name',
                                    'Value': last_name
                                },
                                {
                                    'Name': 'custom:business_name',
                                    'Value': company_name
                                },
                                {
                                    'Name': 'custom:contact_number',
                                    'Value': company_phone
                                },
                                {
                                    'Name': 'custom:address',
                                    'Value': company_address
                                },
                                {
                                    'Name': 'custom:address_2',
                                    'Value': company_address_2
                                },
                                {
                                    'Name': 'custom:postal_code',
                                    'Value': company_zip_code
                                },
                                {
                                    'Name': 'custom:city',
                                    'Value': company_city
                                },
                                {
                                    'Name': 'custom:state',
                                    'Value': company_state
                                },
                                {
                                    'Name': 'custom:account_number',
                                    'Value': account_number
                                },
                                {
                                    'Name': 'custom:user_id',
                                    'Value': str(uid)
                                },
                                {
                                    'Name': 'custom:login_name',
                                    'Value': username
                                },
                            ],
                            TemporaryPassword=password,
                            ForceAliasCreation=False,
                            MessageAction='SUPPRESS')

                        set_user_password_response = _client.admin_set_user_password(
                            UserPoolId=Config.COGNITO_USERPOOL_ID,
                            Username=f"{get_user_data.get('LoginName', '').strip().replace(' ', '')}{get_user_data.get('CustID', '')}",
                            Password=password,
                            Permanent=True)

                        update_attribute_response = _client.admin_update_user_attributes(
                            UserPoolId=Config.COGNITO_USERPOOL_ID,
                            Username=f"{get_user_data.get('LoginName', '').strip().replace(' ', '')}{get_user_data.get('CustID', '')}",
                            UserAttributes=[
                                {
                                    'Name': 'email_verified',
                                    'Value': 'true'
                                },
                            ])
                        return custom_response("success", "User Added.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Username or Password are incorrect.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.InvalidPasswordException:
            return custom_response("error", "Invalid password.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UsernameExistsException:
            return custom_response("error", "Username exists.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/resend_confirmation_code")
class ResendConfirmationCode(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        username = payload.get('username', '')
        try:
            response = _client.resend_confirmation_code(
                ClientId=Config.COGNITO_APP_CLIENT_ID,
                Username=username
            )
            return custom_response("success", "Code sent.", HTTPStatus.OK)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.LimitExceededException:
            return custom_response("error", "Limit exceeded.", HTTPStatus.TOO_MANY_REQUESTS)
        except _client.exceptions.CodeDeliveryFailureException:
            return custom_response("error", "Code was not delivered.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "User not Authorized", HTTPStatus.UNAUTHORIZED)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)


@auth_ns.route("/update_user_preferences")
class UpdateUserPreferences(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        billing_ref_required = payload.get('billing_ref_required', '')
        use_saved_billing_ref = payload.get('use_saved_billing_ref', '')
        email_delivery_notification = payload.get('email_delivery_notification', '')
        print_published_rates = payload.get('print_published_rates', '')
        default_service = payload.get('default_service', '')
        print_to = payload.get('print_to', '')
        handling_fee = payload.get('handling_fee', '')

        user_data = request.data

        if billing_ref_required != "1":
            billing_ref_required = "0"

        if use_saved_billing_ref != "1":
            use_saved_billing_ref = "0"

        if email_delivery_notification != "1":
            email_delivery_notification = "0"

        if print_published_rates != "1":
            print_published_rates = "0"

        if handling_fee == "":
            handling_fee = 0

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            update_user_profile_query = f"UPDATE UserProfile SET BillingRefRequired='{billing_ref_required}', " \
                                        f"EmailPOD='{email_delivery_notification}', DefaultService='{default_service}', " \
                                        f"UseLocBillingRef='{use_saved_billing_ref}', PrintToLabel='{print_to}', " \
                                        f"HandlingFee='{handling_fee}', PrintPublishedRates='{print_published_rates}' " \
                                        f"WHERE UID='{user_data.get('user_id')}'"

            app_db.execute_query(cursor, update_user_profile_query)
            app_db.commit_connection(conn)

            return custom_response("success", "Data Updated", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/force_change_password")
class ForceChangePassword(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        user_data = request.data
        new_password = payload.get('new_password', '')
        account_number = user_data.get('account_number', '')
        username = user_data.get('login_name', '')

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            response = _client.change_password(
                PreviousPassword='Dummy@1234',
                ProposedPassword=new_password,
                AccessToken=request.headers['X-LSO-Authorization'].split(' ')[1]
            )

            password_change_query = f"UPDATE UserProfile SET UserPWD='{new_password}', PWDResentCount='0', " \
                                    f"PWDChangedLast=getdate() WHERE CustId={account_number} AND " \
                                    f"UPPER(LoginName)='{username}'"

            app_db.execute_query(cursor, password_change_query)
            app_db.commit_connection(conn)

            return custom_response("success", "Password successfully changed.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except _client.exceptions.InvalidParameterException:
            return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.InvalidPasswordException:
            return custom_response("error", "Invalid password.", HTTPStatus.BAD_REQUEST)
        except _client.exceptions.NotAuthorizedException:
            return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
        except _client.exceptions.LimitExceededException:
            return custom_response("error", "Limit exceeded.", HTTPStatus.TOO_MANY_REQUESTS)
        except _client.exceptions.UserNotFoundException:
            return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
        except _client.exceptions.UserNotConfirmedException:
            return custom_response("error", "User not confirmed.", HTTPStatus.BAD_REQUEST)
        except ParamValidationError:
            return custom_response("error", "New password must contain upper, lower, and digit and 8 characters long",
                                   HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "An unexpected error occurred, Please try again.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@auth_ns.route("/confirm_email")
class ConfirmEmail(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = auth_ns.payload or {}
        user_data = request.data

        email = strip_specials(payload.get('email', ''))

        if validate_email(email=email):
            conn = app_db.create_connection()
            cursor = app_db.create_cursor(conn)

            try:
                response = _client.admin_update_user_attributes(
                    UserPoolId=Config.COGNITO_USERPOOL_ID,
                    Username=f"{user_data.get('login_name').strip().replace(' ', '')}{user_data.get('account_number')}",
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': email
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        },
                    ]
                )
                update_email_query = f"UPDATE UserProfile SET USerEmail='{email}' " \
                                     f"WHERE UID='{user_data.get('user_id')}'"
                app_db.execute_query(cursor, update_email_query)
                app_db.commit_connection(conn)
                return custom_response("success", "Email Confirmed.", HTTPStatus.OK)
            except _mssql.MssqlDatabaseException:
                return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
            except _client.exceptions.InvalidParameterException:
                return custom_response("error", "Invalid parameter.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.NotAuthorizedException:
                return custom_response("error", "Not authorized.", HTTPStatus.UNAUTHORIZED)
            except _client.exceptions.CodeDeliveryFailureException:
                return custom_response("error", "Code was not delivered.", HTTPStatus.BAD_REQUEST)
            except _client.exceptions.UserNotFoundException:
                return custom_response("error", "User not found.", HTTPStatus.NOT_FOUND)
            except _client.exceptions.UserNotConfirmedException:
                return custom_response("error", "User not confirmed.", HTTPStatus.UNAUTHORIZED)
            except _client.exceptions.AliasExistsException:
                return custom_response("error", "New email are already in use", HTTPStatus.UNAUTHORIZED)
            except Exception as e:
                return custom_response("error", "An unexpected error occurred, Please try again.",
                                       HTTPStatus.BAD_REQUEST)
            finally:
                app_db.close_connection(conn)
        else:
            return custom_response("error", "Email is not in valid format.", HTTPStatus.BAD_REQUEST)


@auth_ns.route("/check_user_profile")
class CheckUserProfile(Resource):
    def post(self):
        payload = auth_ns.payload or {}
        account_number = strip_specials(payload.get('account_number', ''))

        if not check_user_profile(account_number):
            return custom_response("error", "Not valid", HTTPStatus.BAD_REQUEST)
        else:
            return custom_response("success", "Valid", HTTPStatus.OK)
