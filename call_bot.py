import json
import time
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import zoom_api
from config import *
from medsenger_api import *
import jwt
from jose import jws
from zoom_api import createMeeting

medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, debug=True)
app = Flask(__name__)
CORS(app)


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


@app.route('/status', methods=['POST'])
def status():
    data = request.json

    if data['api_key'] != APP_KEY:
        return 'invalid key'

    answer = {
        "is_tracking_data": False,
        "supported_scenarios": [],
        "tracked_contracts": []
    }

    return json.dumps(answer)


@app.route('/init', methods=['POST'])
def init():
    return 'ok'


@app.route('/remove', methods=['POST'])
def remove():
    return 'ok'


@app.route('/settings', methods=['GET'])
def settings():
    key = request.args.get('api_key', '')

    if key != APP_KEY:
        return "<strong>Некорректный ключ доступа.</strong> Свяжитесь с технической поддержкой."

    return render_template('settings.html')

@app.route('/check/<call_id>', methods=['GET'])
def check_call(call_id):
    calls = {}
    try:
        with open('call.json', 'r') as file:
            calls = json.loads(file.read())
    except:
        pass

    if not calls or int(call_id) in calls.values():
        return jsonify({
            "status": "active"
        })
    else:
        return jsonify({
            "status": "ended"
        })

@app.route('/<call_id>/<call_pass>', methods=['GET'])
def call(call_id, call_pass):
    sign = get_sign(call_id)

    calls = {}
    try:
        with open('call.json', 'r') as file:
            calls = json.loads(file.read())
    except:
        pass

    if not calls or int(call_id) in calls.values():
        return render_template('call.html', call_id=call_id, call_pass=call_pass, signature=sign, api_key=ZOOM_KEY)
    else:
        return "<h1>Эта конференция уже завершена.</h1>"


@app.route('/call', methods=['GET'])
def create_call():
    key = request.args.get('api_key', '')
    contract_id = request.args.get('contract_id', '')

    if key != APP_KEY:
        return "<strong>Некорректный ключ доступа.</strong> Свяжитесь с технической поддержкой."

    info = medsenger_api.get_patient_info(contract_id)
    key = info.get('doctor_zoom_key')
    sec = info.get('doctor_zoom_sec')

    if not key or not sec:
        key, sec = DEFAULT_ACCOUNT
        # return "Видеозвонки не настроены."

    calls = {}
    try:
        with open('call.json', 'r') as file:
            calls = json.loads(file.read())
    except:
        pass

    last_number = calls.get(key, '')
    if last_number:
        zoom_api.endMeeting(key, sec, last_number)

    number, password, host_key, join_url = createMeeting(key, sec)
    call_url = "https://call.medsenger.ru/{}/{}".format(number, password)
    medsenger_api.send_message(contract_id, "Видеозвонок от врача.", action_link=call_url, action_type="zoom", action_name="Подключиться к конференции", send_from="doctor",
                               action_deadline=int(time.time() + 60 * 25), action_big=True)
    medsenger_api.send_message(contract_id, "Для подключения через приложение Zoom:\n - номер конференции: {}\n - пароль: {}\n - ключ организатора: {}\n\n<a href='{}' target='_blank'>{}</a>\n\nДля ввода ключа организатора нажмите <i>Участники -> Подробнее -> Принять роль организатора</i>.".format(number, password, host_key, join_url, join_url), only_doctor=True, action_deadline=int(time.time() + 60 * 25))

    calls[key] = number

    with open('call.json', 'w') as file:
        file.write(json.dumps(calls))

    return render_template('start.html', call_url=call_url, number=number, password=password, join_url=join_url)

@app.route('/close', methods=['GET'])
def close():
    return render_template('close.html')

@app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


@app.route('/message', methods=['POST'])
def save_message():
    return "ok"


if __name__ == "__main__":
    app.run(port=PORT, host=HOST)
