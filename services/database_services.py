import pymssql


class AppDatabaseController(object):
    def __init__(self, config):
        self.server = config.APP_DATABASE_SERVER
        self.database = config.APP_DATABASE
        self.user = config.APP_DATABASE_USER
        self.password = config.APP_DATABASE_PASS

    def create_connection(self):
        return pymssql.connect(server=self.server, user=self.user, password=self.password, database=self.database)

    def create_cursor(self, connection):
        return connection.cursor(as_dict=True)

    def execute_query(self, cursor, query):
        return cursor.execute(query)

    def commit_connection(self, connection):
        return connection.commit()

    def close_connection(self, connection):
        return connection.close()

    def rollback_connection(self, connection):
        return connection.rollback()

    def create_cursor_without_dict(self, connection):
        return connection.cursor()

    async def execute_query_async(self, cursor, query):
        return cursor.execute(query)


class OpsDatabaseController(object):
    def __init__(self, config):
        self.server = config.OPS_DATABASE_SERVER
        self.database = config.OPS_DATABASE
        self.user = config.OPS_DATABASE_USER
        self.password = config.OPS_DATABASE_PASS

    def create_connection(self):
        return pymssql.connect(server=self.server, user=self.user, password=self.password, database=self.database)

    def create_cursor(self, connection):
        return connection.cursor(as_dict=True)

    def execute_query(self, cursor, query):
        return cursor.execute(query)

    def commit_connection(self, connection):
        return connection.commit()

    def close_connection(self, connection):
        return connection.close()

    def rollback_connection(self, connection):
        return connection.rollback()

    def create_cursor_without_dict(self, connection):
        return connection.cursor()

    async def execute_query_async(self, cursor, query):
        return cursor.execute(query)
