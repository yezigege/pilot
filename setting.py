# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
load_dotenv(override=True)

DEBUG = True
BASE_DIR = os.getcwd()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DECODE_RESPONSES = True
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
