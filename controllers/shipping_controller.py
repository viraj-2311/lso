from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import ops_db, app_db
from services.soap_requests.shipping_service import retrieve_service_types, retrieve_service_type_by_zip_code, check_zip
from utilities import custom_response, strip_specials, get_city_state_func, zip_inside_core_service_area, \
    service_allowed_override, service_type_dict

shipping_service_ns = Namespace("/shipping_service", description="Shipping related operations")


@shipping_service_ns.route("/retrieve_service_types")
class RetrieveServiceType(Resource):
    def get(self):
        try:
            service_types = retrieve_service_types()

            if service_types[1] == "success":
                return custom_response("success", "Service types.", HTTPStatus.OK, data=service_types[0])
            elif service_types[1] == "error":
                return custom_response("error", service_types[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@shipping_service_ns.route("/retrieve_service_types_by_zip")
class RetrieveServiceTypeByZip(Resource):
    def post(self):
        try:
            payload = shipping_service_ns.payload or {}
            from_zip = strip_specials(payload.get("from_zip", "")).strip()
            to_zip = strip_specials(payload.get("to_zip", "")).strip()

            service_types = retrieve_service_type_by_zip_code(from_zip=from_zip, to_zip=to_zip)

            if service_types[1] == "success":
                return custom_response("success", "Service types.", HTTPStatus.OK, data=service_types[0])
            elif service_types[1] == "error":
                return custom_response("error", service_types[0], HTTPStatus.BAD_REQUEST)
            else:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@shipping_service_ns.route("/check_zip")
class CheckZip(Resource):
    def post(self):
        try:
            payload = shipping_service_ns.payload or {}
            zip_code = strip_specials(payload.get("zip_code", "")).strip()
            country_code = strip_specials(payload.get("country_code", "")).strip()

            if country_code != "UnitedStates" and country_code != "MX":
                country_code = "UnitedStates"

            get_city_state = get_city_state_func(zip_code=zip_code, country=country_code)

            if get_city_state:
                return {"valid": "true"}, 200
            else:
                return {"valid": "false"}, 200
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@shipping_service_ns.route("/service_by_zip")
class ServiceByZip(Resource):
    def get(self):
        try:
            args = request.args
            zip_code = strip_specials(args.get("zip_code", "")).strip()
            country = strip_specials(args.get("country", "")).strip()
            account_number = strip_specials(args.get("account_number", "0")).strip()
            user_id = strip_specials(args.get("user_id", "0")).strip()

            if country != "UnitedStates" and country != "MX":
                country = "UnitedStates"

            get_city_state = get_city_state_func(zip_code=zip_code, country=country, account_number=account_number,
                                                 user_id=user_id)
            if get_city_state:
                data = {
                    "city": get_city_state.get("Cityname", "").strip(),
                    "state": get_city_state.get("State", "").strip(),
                    "zipcode": zip_code
                }
                return data, 200
            else:
                return custom_response("error", "Please enter valid zip code.", HTTPStatus.BAD_REQUEST)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)


@shipping_service_ns.route("/get_allowed_services")
class GetAllowedServices(Resource):
    def get(self):
        args = request.args
        from_zip = strip_specials(args.get("from_zip", "")).strip()
        to_zip = strip_specials(args.get("to_zip", "")).strip()
        to_country_code = strip_specials(args.get("to_country_code", "")).strip()

        validate_from_zip = check_zip(from_zip=from_zip, to_zip=from_zip)
        validate_to_zip = check_zip(from_zip=to_zip, to_zip=to_zip)

        if validate_from_zip[1] == "success":
            validate_from_zip = True
        else:
            validate_from_zip = False

        if validate_to_zip[1] == "success":
            validate_to_zip = True
        else:
            validate_from_zip = False

        allowed_services_list = []

        if validate_from_zip and validate_to_zip:
            start_in_core = zip_inside_core_service_area(from_zip)
            end_in_core = zip_inside_core_service_area(to_zip)

            allowed_overrides = service_allowed_override(from_zip=from_zip, to_zip=to_zip)

            conn = ops_db.create_connection()
            cursor = ops_db.create_cursor(conn)

            try:
                service_type_query = "SELECT ss.ServiceID, ss.InsideIn, ss.OutsideOut, ss.InsideOut, ss.OutsideIn, " \
                                     "sa.MarketingName as ServDescription, sa.AddlDescription1, sa.AddlDescription2, " \
                                     "sa.ServiceClass, sa.SelectionOrder FROM StdServiceType ss INNER JOIN " \
                                     "ServiceAddlInfo sa ON ss.ServiceID = sa.ServiceID WHERE sa.Visible = 1 " \
                                     "ORDER BY sa.ViewOrder"
                ops_db.execute_query(cursor, service_type_query)
                service_type = cursor.fetchall()
                for services in service_type:
                    allowed_services = dict()
                    service_id = services.get("ServiceID", "")
                    service_description = services.get("ServDescription", "")
                    allowed_services["service_id"] = service_id
                    allowed_services["label"] = service_description
                    allowed_services["addl_description_1"] = services.get("AddlDescription1", "")
                    allowed_services["addl_description_2"] = services.get("AddlDescription2", "")
                    allowed_services["service_class"] = services.get("ServiceClass", "")
                    allowed_services["selection_order"] = services.get("SelectionOrder", "")
                    if service_description == "LSO  2nd Day":
                        service_description = "LSO 2nd Day"
                    allowed_services["name"] = service_type_dict[service_description]

                    if allowed_overrides.get(service_id) == 2:
                        allowed_services["allowed"] = False
                    elif start_in_core and end_in_core and services.get("InsideIn", ""):
                        allowed_services["allowed"] = True
                    elif not start_in_core and not end_in_core and services.get("OutsideOut", ""):
                        allowed_services["allowed"] = True
                    elif start_in_core and not end_in_core and services.get("InsideOut", ""):
                        if to_country_code != "MX":
                            allowed_services["allowed"] = True
                        else:
                            allowed_services["allowed"] = False
                    elif not start_in_core and end_in_core and services.get("OutsideIn", ""):
                        allowed_services["allowed"] = True
                    elif allowed_overrides.get(service_id) == 1:
                        allowed_services["allowed"] = True
                    else:
                        if to_country_code == "MX" and service_id == "M":
                            allowed_services["allowed"] = True
                        else:
                            allowed_services["allowed"] = False
                    allowed_services_list.append(allowed_services)

                return {"response": allowed_services_list}, 200
            except _mssql.MssqlDatabaseException:
                return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
            except Exception as e:
                return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
            finally:
                ops_db.close_connection(conn)
        else:
            return {"response": allowed_services_list}, 200


@shipping_service_ns.route("/get_service_list")
class GetServiceList(Resource):
    def get(self):
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            service_list_query = "SELECT ServiceID, ServDescription FROM StdServiceType WHERE ServiceID NOT IN ('T', 'N')"
            app_db.execute_query(cursor, service_list_query)
            service_list = cursor.fetchall()
            return {"response": service_list}, 200
        except _mssql.MssqlDatabaseException:
            return {}, 400
        finally:
            app_db.close_connection(conn)
