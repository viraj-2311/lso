from http import HTTPStatus

from flask import request
from flask_cognito import cognito_auth_required
from flask_restx import Namespace, Resource
from pymssql import _mssql

from main import app_db
from utilities import custom_response, strip_specials, get_user_data

group_maintenance_ns = Namespace("/group_maintenance", description="Group maintenance related operation")


def validate_new_group(group_name, user_id):
    conn = app_db.create_connection()
    cursor = app_db.create_cursor(conn)

    group_exist_query = f"SELECT GroupName FROM IGroup WHERE GroupName='{group_name}' and " \
                        f"UID='{user_id}'"
    try:
        app_db.execute_query(cursor, group_exist_query)
        if cursor.fetchall():
            return cursor.fetchall()
    except _mssql.MssqlDatabaseException as e:
        return None
    finally:
        app_db.close_connection(conn)


@group_maintenance_ns.route("/create_group")
class CreateGroup(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = group_maintenance_ns.payload or {}
        group_name = strip_specials(payload.get('group_name', ''))
        group_description = strip_specials(payload.get('group_description', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:
            if not group_name:
                return custom_response("error", "You may not enter a blank Group Name.", HTTPStatus.BAD_REQUEST)
            elif not group_description:
                return custom_response("error", "You may not enter a blank Group Description.", HTTPStatus.BAD_REQUEST)
            else:
                if validate_new_group(group_name, user_data.get('user_id', '')):
                    return custom_response("error", "Group Name already exists. Please select a different Group Name.",
                                           HTTPStatus.BAD_REQUEST)
                else:
                    check_group_query = f"SELECT * FROM IGroup WHERE UID='{user_data.get('user_id')}' " \
                                        f"AND GroupName='{group_name.upper()}'"

                    app_db.execute_query(cursor, check_group_query)
                    check_group = cursor.fetchall()
                    if check_group:
                        return custom_response("error", "Group Name already exists", HTTPStatus.BAD_REQUEST)
                    else:
                        add_group_query = f"INSERT IGroup (UID, GroupName, GroupDescr) VALUES " \
                                          f"('{user_data.get('user_id', '')}'," \
                                          f"'{group_name.upper()}', '{group_description.upper()}')"

                        app_db.execute_query(cursor, add_group_query)
                        app_db.commit_connection(conn)

                        return custom_response("success", f"Group Name {group_name} has been created.", HTTPStatus.OK)
        except (KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/get_group")
class GetGroup(Resource):
    @get_user_data
    @cognito_auth_required
    def get(self):
        args = request.args
        with_members = False
        if args.get('withMembers') == 'true':
            with_members = True
        user_data = request.data
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if with_members:
                get_group_data_query = "SELECT DISTINCT IG.GroupId, IG.UID, IG.GroupName, IG.GroupDescr," \
                                       "(SELECT COUNT(*) FROM dbo.GroupMembers WHERE GroupId = IG.GroupId) as MC " \
                                       "FROM dbo.GroupMembers GM JOIN dbo.IGroup IG ON IG.GroupId = GM.GroupId " \
                                       f"WHERE IG.UID ='{user_data.get('user_id', '')}'"
                app_db.execute_query(cursor, get_group_data_query)
            else:
                get_group_data_query = "SELECT IG.GroupId, IG.UID, IG.GroupName, IG.GroupDescr," \
                                       "(SELECT COUNT(*) FROM GroupMembers GM WHERE GM.GroupId = IG.GroupId) as MC " \
                                       f"FROM IGroup IG WHERE UID='{user_data.get('user_id', '')}'"
                app_db.execute_query(cursor, get_group_data_query)

            get_group_data = cursor.fetchall()
            if get_group_data:
                return custom_response("success", "Group list.", HTTPStatus.OK, data=get_group_data)
            else:
                return custom_response("success", "No Groups", HTTPStatus.OK, data=dict())
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/delete_group")
class DeleteGroup(Resource):
    @get_user_data
    @cognito_auth_required
    def post(self):
        payload = group_maintenance_ns.payload or {}
        group_name = strip_specials(payload.get('group_name', ''))
        group_id = strip_specials(payload.get('group_id', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:

            if not group_name:
                return custom_response("error", "Please select a valid Group Name to delete.", HTTPStatus.BAD_REQUEST)
            else:
                delete_group_member_query = f"DELETE GroupMembers WHERE GroupId='{group_id}'"
                app_db.execute_query(cursor, delete_group_member_query)
                app_db.commit_connection(conn)

                delete_group_query = f"DELETE IGroup WHERE UID='{user_data.get('user_id', '')}' and GroupName='{group_name}'"
                app_db.execute_query(cursor, delete_group_query)
                app_db.commit_connection(conn)
                return custom_response("success", f"Group Name {group_name} has been deleted from the system.",
                                       HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except Exception as e:
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/get_group_members")
class GetGroupMembers(Resource):
    @get_user_data
    @cognito_auth_required
    def get(self):
        args = request.args
        group_id = strip_specials(args.get('group_id', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        user_data = request.data
        try:
            get_members_query = f"SELECT GM.GroupId, GM.QuickCode, W.*, Coalesce(W.CountryCode, 'US') AS " \
                                f"CountryCode FROM GroupMembers GM JOIN WebLocation W ON GM.QuickCode=W.QuickCode " \
                                f"AND W.UID='{user_data.get('user_id', '')}' WHERE GM.GroupId='{group_id}' " \
                                f"ORDER BY GM.QuickCode ASC"

            app_db.execute_query(cursor, get_members_query)
            get_members = cursor.fetchall()
            if len(get_members):
                return custom_response("success", "Members list.", HTTPStatus.OK, data=get_members)
            else:
                return custom_response("success", "No members", HTTPStatus.OK, data=dict())
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/remove_group_members")
class RemoveMembers(Resource):
    @cognito_auth_required
    def post(self):
        members = ''
        payload = group_maintenance_ns.payload or {}
        group_name = strip_specials(payload.get('group_name', '')).strip()
        group_member_list = payload.get('group_member_list', '')
        group_id = strip_specials(payload.get('group_id', ''))

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            if not group_name:
                return custom_response("error", "Please select a valid Group Name.", HTTPStatus.BAD_REQUEST)
            else:
                for gm_value in group_member_list:
                    if gm_value:
                        members = f"{members} QuickCode='{gm_value}' or"

                if len(members) > 3:
                    members = members[:-3]

                delete_member_query = f"DELETE FROM GroupMembers WHERE GroupId={group_id} " \
                                      f"AND ({members})"
                app_db.execute_query(cursor, delete_member_query)
                app_db.commit_connection(conn)

                return custom_response("success", f"Group Members are now deleted from group {group_name}.",
                                       HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/add_group_members")
class AddMembers(Resource):
    @cognito_auth_required
    def post(self):
        maximum = 100
        num_add = 0
        payload = group_maintenance_ns.payload or {}
        group_name = strip_specials(payload.get('group_name', '')).strip()
        quick_code_list = payload.get('quick_code_list', '')
        group_id = strip_specials(payload.get('group_id', ''))
        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:

            if not group_name:
                return custom_response("error", "Please select a valid Group Name.", HTTPStatus.BAD_REQUEST)
            else:
                for quick_code in quick_code_list:
                    if quick_code:
                        num_add += 1

                if num_add > maximum:
                    return custom_response("error", f"You have exceeded the limit of {maximum} "
                                                    "members in group. Members were not added.", HTTPStatus.BAD_REQUEST)

                for quick_code in quick_code_list:
                    if quick_code:
                        member_exist_query = f"SELECT * FROM GroupMembers WHERE QuickCode='{quick_code}' AND " \
                                             f"GroupId={group_id}"
                        app_db.execute_query(cursor, member_exist_query)
                        member_exist = cursor.fetchall()

                        if not member_exist:
                            add_member_query = f"INSERT INTO GroupMembers (GroupId, QuickCode) VALUES " \
                                               f"('{group_id}', '{quick_code}')"
                            app_db.execute_query(cursor, add_member_query)
                            app_db.commit_connection(conn)
                            member_exist = None

                return custom_response("success", f"Group Members are now added to group {group_name}.", HTTPStatus.OK)
        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
        except (IndexError, KeyError, Exception):
            return custom_response("error", "Oops! An unexpected error occurred.", HTTPStatus.BAD_REQUEST)
        finally:
            app_db.close_connection(conn)


@group_maintenance_ns.route("/get_all_group_members")
class GetAllGroupMembers(Resource):
    @get_user_data
    @cognito_auth_required
    def get(self):
        user_data = request.data

        conn = app_db.create_connection()
        cursor = app_db.create_cursor(conn)

        try:
            get_all_group_members_query = "SELECT WL.QuickCode, IG.GroupID, WL.Name, WL.CountryCode FROM IGroup IG " \
                                          "JOIN GroupMembers GM ON IG.GroupId=GM.GroupId JOIN WebLocation WL ON " \
                                          "WL.QuickCode=GM.QuickCode AND WL.UID=IG.UID WHERE " \
                                          f"IG.UID='{user_data.get('user_id', '')}' ORDER BY IG.GroupId"
            app_db.execute_query(cursor, get_all_group_members_query)

            get_all_group_member = cursor.fetchall()

            if get_all_group_member:
                return custom_response("success", "Group list.", HTTPStatus.OK, data=get_all_group_member)
            else:
                return custom_response("success", "No Groups", HTTPStatus.OK, data=dict())

        except _mssql.MssqlDatabaseException:
            return custom_response("error", "Database Error", HTTPStatus.BAD_GATEWAY)
