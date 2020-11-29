from flask import Flask
import logging

from utils.log.config import LogName
from utils.log.log import pilot_handler, get_logger


loggers = [(LogName.pilot.name, logging.DEBUG, logging.INFO, pilot_handler)]
pilot_logger = get_logger(LogName.pilot.name)


def config_loggers(app):
    # Configure logging for libs to help debug
    for logger_name, debug_level, production_level, handler in loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        if app.debug:
            logger.setLevel(debug_level)
        else:
            logger.setLevel(production_level)


def create_app():
    # 创建Flask对象
    app = Flask(__name__, template_folder='templates')
    # 注册蓝图
    from service.route import pilot
    app.register_blueprint(pilot)

    config_loggers(app)
    return app

