from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource

from services.tracking_service import track_barcode
from utilities import custom_response

tracking_service_ns = Namespace("/tracking", description="Tracking related operations")


@tracking_service_ns.route("/track_barcode")
class TrackBarcode(Resource):

    def get(self):
        """
        Take barcode from GET params and fetch tracking details for that barcode(s)
        :return: custom_response with tracking details in JSON
        """
        barcodes = request.args.get('barcodes')

        if not barcodes:
            custom_response("Error", "Please provide valid barcodes", HTTPStatus.BAD_REQUEST)

        if ',' in barcodes:
            barcodes = barcodes.split(',')
        else:
            barcodes = [barcodes]

        tracking_details_json = []
        for barcode in barcodes:
            result = track_barcode(barcode)
            try:
                result['Package']['overallstatus'] = result['Package']['scanevents'][0]['statusdescription']
            except IndexError:
                pass
            tracking_details_json.append(result)
        # tracking_details_json = [track_barcode(barcode) for barcode in barcodes]
        return custom_response("Success", tracking_details_json, HTTPStatus.OK)
