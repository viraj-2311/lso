from flask_cognito import CognitoAuth
from flask_restx import Namespace, Resource

from controllers.addressbook_controller import addressbook_ns
from controllers.auth_controller import auth_ns
from controllers.fuel_surcharge_controller import fuel_surcharge_ns
from controllers.group_maintenance_controller import group_maintenance_ns
from controllers.locator_service_controller import locator_service_ns
from controllers.news_controller import news_ns
from controllers.order_supplies_controller import order_supplies_ns
from controllers.pickup_service_controller import pickup_service_ns
from controllers.pod_service_controller import pod_service_ns
from controllers.pricing_service_controller import pricing_service_ns
from controllers.printing_service_controller import printing_service_ns
from controllers.reports_service_controller import reports_service_ns
from controllers.shipping_controller import shipping_service_ns
from controllers.tracking_service_controller import tracking_service_ns
from controllers.cookie_program_controller import cookie_program_ns
from controllers.payfabric_service_controller import payfabric_service_ns

from main import api, app

root_ns = Namespace('root')

api.add_namespace(root_ns, path='')
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(addressbook_ns, path='/addressbook')
api.add_namespace(group_maintenance_ns, path='/group_maintenance')
api.add_namespace(shipping_service_ns, path='/shipping_service')
api.add_namespace(printing_service_ns, path='/printing_service')
api.add_namespace(locator_service_ns, path='/locator_service')
api.add_namespace(pricing_service_ns, path='/pricing_service')
api.add_namespace(reports_service_ns, path='/reports_service')
api.add_namespace(pickup_service_ns, path='/pickup_service')
api.add_namespace(fuel_surcharge_ns, path='/fuel_surcharge')
api.add_namespace(order_supplies_ns, path='/order_supplies')
api.add_namespace(tracking_service_ns, path='/tracking')
api.add_namespace(cookie_program_ns, path='/cookieprogram')
api.add_namespace(pod_service_ns, path='/pod_service')
api.add_namespace(news_ns, path='/news')
api.add_namespace(payfabric_service_ns, path='/payment')
application = app
cog_auth = CognitoAuth(app)


@root_ns.route("/")
class root(Resource):
    def get(self):
        return {'status': 1, 'response': 'LSO API'}


if __name__ == '__main__':
    application.run()
