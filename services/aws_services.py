import boto3


class AwsCognitoController(object):
    def __init__(self, config):
        self.client = boto3.client('cognito-idp', region_name=config.COGNITO_REGION,
                                   aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)


class AwsS3Controller(object):
    def __init__(self, config):
        self.s3 = boto3.client('s3', region_name=config.COGNITO_REGION)


class AwsLambdaController(object):
    def __init__(self, config):
        self.aws_lambda = boto3.client('lambda', region_name=config.COGNITO_REGION,
                                       aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                                       aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)
