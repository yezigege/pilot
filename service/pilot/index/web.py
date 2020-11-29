from flask_restx import Resource, Namespace
from flask import request, jsonify, make_response


ns = Namespace("pilot", description="pilot page")


@ns.route('')
class IndexHandler(Resource):

    def get(self):
        return "hello world"
