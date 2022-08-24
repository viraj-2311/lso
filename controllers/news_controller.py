from http import HTTPStatus

from flask_restx import Namespace, Resource

from services.news_services import get_featured_news
from utilities import custom_response

news_ns = Namespace("news", description="News related services")


@news_ns.route("/get_featured_news")
class GetFeaturedNews(Resource):
    def get(self):
        response = get_featured_news()
        response_list = []
        for items in response['items']:
            if items['is-this-a-feature-blog']:
                response_list.append(items)
        return custom_response("success", "Featured News", HTTPStatus.OK, data=response_list)
