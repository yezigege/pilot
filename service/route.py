from utils.blueprint import create_blueprint
from flask_restx import Api
from service.pilot.index.web import ns as index_ns


pilot = create_blueprint('pilot', __name__, url_prefix='/api')

api = Api(pilot, version='1.0', title='pilot service',
          description='pilot service for me'
          )

api.add_namespace(index_ns)
