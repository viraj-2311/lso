from flask import Flask
from flask_cognito import CognitoAuthError
from flask_cors import CORS
from flask_restx import Api

from config import Config
from services.service_manager import ServiceManager

app = Flask(__name__, template_folder='static', static_url_path='/static')
app.config.from_object('config.Config')
service_manager = ServiceManager(Config)
app_db = service_manager.app_db
ops_db = service_manager.ops_db
soap = service_manager.soap

cors = CORS(app, origins=[
    "http://localhost",
    "http://localhost:*",
    "http://127.0.0.1:*",
    "http://0.0.0.0:*",
    "https://d10u3247w5ubs0.cloudfront.net",
    "https://frontend-prod.lso.com",
    "https://api-dev.lso.com",
    "https://api-prod.lso.com",
    "https://app.lso.com",
    "https://staging-app.lso.com",
    "https://d1oqqgixk9wrjh.cloudfront.net",
    "https://dev-app.lso.com"
])

api = Api(
    app,
    security="Bearer Auth",
    version="1",
    title="LSO API",
    description="LSO API"
)


class CustomError(Exception):
    def __init__(self, error, description, status_code=401, headers=None):
        self.error = error
        self.description = description
        self.status_code = status_code
        self.headers = headers

    def __repr__(self):
        return f'CustomError: {self.error}'

    def __str__(self):
        return f'{self.error} - {self.description}'


@api.errorhandler(CognitoAuthError)
@api.errorhandler(CustomError)
def custom_error(error):
    if str(error) == "Invalid Cognito Authentication Token - Token is expired":
        return {"status": "error", "message": "TokenExpiredError"}
    elif "Authorization Required" in str(error):
        return {"status": "error", "message": "AccessTokenRequiredError"}
    elif "InvalidTokenError" in str(error):
        return {"status": "error", "message": "InvalidTokenError"}
    elif "Malformed Authentication Token" in str(error):
        return {"status": "error", "message": "InvalidTokenError"}
