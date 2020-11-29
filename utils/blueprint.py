from flask import Blueprint, request, after_this_request
import time

from utils.log.config import LogName
from service import get_logger


def create_blueprint(name, package_name, url_prefix):
    bp = Blueprint(name, package_name, url_prefix=url_prefix)
    logger = get_logger(LogName.pilot.name)

    @bp.before_request
    def req_pre_logging():
        start = time.time()

        if request.method == 'GET':
            payload = request.args.to_dict()
        else:
            try:
                payload = request.get_json(force=True)
            except Exception as e:
                logger.error(e)
                payload = request.form.to_dict()
        logger.info('\t'.join(['REQUEST: {0}:{1}'.format(request.method, request.url),
                               'HEADERS:{0}'.format(dict(request.headers)),
                               'DATA:{0}'.format(payload)]))

        @after_this_request
        def req_post_logging(response):
            att_dict = getattr(response, '__dict__', '')
            resp = {'headers': str(att_dict['headers']),
                    'code': str(att_dict['_status'])
                    }
            try:
                data = att_dict['response'][0].decode('utf-8')
                data = data.replace("\n", "").replace(
                    '\r', '').replace(' ', '')
                resp.update({'data': data})
            except Exception as e:
                logger.error(e)
            logger.info('\t'.join(['RESPONSE: {}'.format(resp),
                                   'TIMECOST: {} ms'.format((time.time() - start) * 1000)]))
            return response

    return bp
