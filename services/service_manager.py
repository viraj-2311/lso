from services.aws_services import AwsCognitoController, AwsS3Controller, AwsLambdaController
from services.database_services import AppDatabaseController, OpsDatabaseController
from services.soap_services import SoapController


class ServiceManager(object):
    def __init__(self, config):
        self.aws_cognito = AwsCognitoController(config)
        self.aws_s3 = AwsS3Controller(config)
        self.aws_lambda = AwsLambdaController(config)
        self.soap = SoapController()
        self.app_db = AppDatabaseController(config)
        self.ops_db = OpsDatabaseController(config)
