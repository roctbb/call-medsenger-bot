import json
import traceback

import jwt
from jose import jws
import os
import sys
import time
from datetime import datetime

from flask import request, abort, render_template
from pytz import timezone
from sentry_sdk import capture_exception
from medsenger_api import AgentApiClient

import zoom_api
from config import *

medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)


def gts():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S - ")


def log(error, terminating=False):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

    if PRODUCTION:
        capture_exception(error)

    if terminating:
        print(gts(), exc_type, file_name, exc_tb.tb_lineno, error, "CRITICAL")
    else:
        print(gts(), exc_type, file_name, exc_tb.tb_lineno, error)


# decorators
def verify_args(func):
    def wrapper(*args, **kwargs):
        if not request.args.get('contract_id'):
            abort(422)
        if request.args.get('api_key') != APP_KEY:
            abort(401)
        try:
            return func(request.args, request.form, *args, **kwargs)
        except Exception as e:
            print(traceback.format_exc())
            log(e, True)
            abort(500)

    wrapper.__name__ = func.__name__
    return wrapper


def verify_json(func):
    def wrapper(*args, **kwargs):
        if not request.json.get('contract_id') and ("status" not in request.url) and ("report" not in request.url):
            abort(422)
        if request.json.get('api_key') != APP_KEY:
            abort(401)
        try:
            return func(request.json, *args, **kwargs)
        except Exception as e:
            log(e, True)
            abort(500)

    wrapper.__name__ = func.__name__
    return wrapper


def get_ui(contract, mode='settings', object_id=None, source=None, params={}):
    return render_template('index.html', contract_id=contract.id, agent_token=contract.agent_token,
                           mode=mode, object_id=object_id, source=source, params=json.dumps(params),
                           api_host=MAIN_HOST.replace('8001', '8000'), local_host=LOCALHOST,
                           agent_id=AGENT_ID, lc=dir_last_updated('static'))


def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))


def timezone_now(zone=None):
    if zone:
        tz = timezone(zone)
    else:
        tz = timezone('Europe/Moscow')
    return datetime.now(tz)


def localize(d, zone=None):
    if zone:
        tz = timezone(zone)
    else:
        tz = timezone('Europe/Moscow')
    return tz.localize(d)


def get_patient_data(contract_id):
    patient = medsenger_api.get_patient_info(contract_id)
    return patient


def get_sign(number):
    iat = int(time.time() - 30)
    exp = iat + 60 * 60 * 2
    oHeader = {"alg": 'HS256', "typ": 'JWT'}

    oPayload = {
        "sdkKey": ZOOM_KEY,
        "mn": number,
        "role": 0,
        "iat": iat,
        "exp": exp,
        "appKey": ZOOM_KEY,
        "tokenExp": iat + 60 * 60 * 2
    }
    return jws.sign(oPayload, ZOOM_SECRET, algorithm="HS256", headers=oHeader)
