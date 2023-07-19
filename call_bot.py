from flask import jsonify
from datetime import timedelta

from managers.ContractsManager import ContractManager
from managers.TimetableManager import TimetableManager
from managers.CallManager import CallManager

from helpers import *
from manage import *

medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, AGENT_ID, API_DEBUG)
contract_manager = ContractManager(medsenger_api, db)
timetable_manager = TimetableManager(medsenger_api, db)
call_manager = CallManager(contract_manager, medsenger_api, db)


@app.route('/')
def index():
    return "Waiting for the thunder"


@app.route('/status', methods=['POST'])
@verify_json
def status(data):
    answer = {
        "is_tracking_data": False,
        "supported_scenarios": [],
        "tracked_contracts": contract_manager.get_active_ids()
    }

    return jsonify(answer)


# contract management api


@app.route('/report', methods=['POST'])
@verify_json
def report(data):
    clinic_id = int(data.get('clinic_id'))
    date_from = int(data.get('from'))
    date_to = int(data.get('to'))
    if not clinic_id:
        abort(422)

    return jsonify([
        {
            "title": "Видеоконсультации",
            "count": call_manager.get_report(clinic_id, date_from, date_to)
        }
    ])


@app.route('/init', methods=['POST'])
@verify_json
def init(data):
    contract_id = data.get('contract_id')
    if not contract_id:
        abort(422)

    engine = data.get('params', {}).get('engine')

    contract, is_new = contract_manager.add(contract_id, engine)
    return "ok"


@app.route('/remove', methods=['POST'])
@verify_json
def remove(data):
    contract_id = data.get('contract_id')
    if not contract_id:
        abort(422)

    contract_manager.remove(contract_id)

    return "ok"


@app.route('/actions', methods=['POST'])
@verify_json
def actions(data):
    print("asked for actions")
    contract = contract_manager.get(data.get('contract_id'))
    actions = []
    if contract.show_timetable:
        actions = [{'link': 'appointment', 'type': 'patient', 'name': 'Записаться на прием'}]

    return jsonify(actions)


# settings and views
@app.route('/settings', methods=['GET'])
@verify_args
def get_settings(args, form):
    contract_id = request.args.get('contract_id', '')

    if contract_manager.not_exists(contract_id):
        contract_manager.add(contract_id)

    contract = contract_manager.get(contract_id)
    return get_ui(contract, 'settings', params={"show_tt": contract.show_timetable})


@app.route('/patient_timetable', methods=['GET'])
@verify_args
def get_patient_timetable(args, form):
    contract_id = request.args.get('contract_id', '')

    if contract_manager.not_exists(contract_id):
        contract_manager.add(contract_id)

    contract = contract_manager.get(contract_id)
    return get_ui(contract, 'calls')


@app.route('/call', methods=['GET'])
@verify_args
def get_call(args, form):
    contract_id = request.args.get('contract_id', '')

    if contract_manager.not_exists(contract_id):
        contract_manager.add(contract_id)

    contract = contract_manager.get(contract_id)
    return get_ui(contract, 'settings')


@app.route('/instant_call', methods=['GET'])
@verify_args
def instant_call(args, form):
    contract_id = request.args.get('contract_id', '')

    if contract_manager.not_exists(contract_id):
        contract_manager.add(contract_id)

    contract = contract_manager.get(contract_id)
    call_manager.start_call(contract_id)
    return get_ui(contract, 'done')


@app.route('/order', methods=['POST'])
@verify_json
def order(data):
    contract_id = data.get('contract_id')
    if contract_manager.not_exists(contract_id):
        contract_manager.add(contract_id)

    if data['order'] == 'start_call':
        if contract_manager.not_exists(contract_id):
            contract_manager.add(contract_id)
        call_manager.start_call(contract_id)
        return 'ok'
    if data['order'] == 'select_call_time':
        medsenger_api.send_message(contract_id, 'Вам необходимо запланировать онлайн-встречу с врачом. ' +
                                   'Для этого воспользуйтесь кнопкой:',
                                   action_name='Выбрать время', action_link='appointment', action_big=False,
                                   only_patient=True, action_onetime=True)
        medsenger_api.send_message(contract_id, 'Пациенту отправлена ссылка на выбор времени консультации.', only_doctor=True)
        return 'ok'

    return 'not found'


@app.route('/appointment', methods=['GET'])
@verify_args
def get_appointment(args, form):
    contract = contract_manager.get(args.get('contract_id'))
    return get_ui(contract, 'appointment')


@app.route('/<call_id>/<call_pass>', methods=['GET'])
def call(call_id, call_pass):
    sign = get_sign(call_id)
    if call_manager.check_call(call_id):
        return render_template('call.html', call_id=call_id, call_pass=call_pass, signature=sign, api_key=ZOOM_KEY)
    else:
        return "<h1>Этот видеозвонок уже завершен.</h1>"


# settings api
@app.route('/api/settings/get_patient/<contract_id>', methods=['GET'])
@verify_args
def get_patient(args, form, contract_id):
    patient = medsenger_api.get_patient_info(contract_id)

    return jsonify(patient)


@app.route('/api/settings/get_doctor_timetable', methods=['GET'])
@verify_args
def get_doctor_tt(args, form):
    contract_id = args.get('contract_id')
    patient = medsenger_api.get_patient_info(contract_id)

    timetable = timetable_manager.get_doctor_timetable(patient['doctor_id'])

    return jsonify(timetable)


@app.route('/api/settings/get_doctor_timetable/<int:start>/<int:days>', methods=['GET'])
@verify_args
def get_doctor_week_tt(args, form, start, days):
    contract_id = args.get('contract_id')
    patient = medsenger_api.get_patient_info(contract_id)

    timetable = timetable_manager.get_doctor_period_timetable(patient['doctor_id'], start, days)

    return jsonify(timetable)


@app.route('/api/settings/get_patient_timetable', methods=['GET'])
@verify_args
def get_patient_tt(args, form):
    contract_id = args.get('contract_id')
    patient = medsenger_api.get_patient_info(contract_id)

    timetable = timetable_manager.get_patient_timetable(patient['id'])

    return jsonify(timetable)


@app.route('/api/settings/save_doctor_timetable', methods=['POST'])
@verify_args
def save_doctor_tt(args, form):
    data = request.json

    slots = []
    for slot in data['slots']:
        s, is_new = timetable_manager.add(slot)
        if s:
            slots.append(s.as_dict())

    return jsonify(slots)


@app.route('/api/settings/show_tt_in_contract', methods=['POST'])
@verify_args
def show_tt_in_contract(args, form):
    contract_id = args.get('contract_id')
    contract_manager.change_show_tt_mode(contract_id, True)

    medsenger_api.update_cache(contract_id)

    return 'ok'


@app.route('/api/settings/hide_tt_in_contract', methods=['POST'])
@verify_args
def hide_tt_in_contract(args, form):
    contract_id = args.get('contract_id')
    contract_manager.change_show_tt_mode(contract_id, False)

    medsenger_api.update_cache(contract_id)
    return 'ok'


@app.route('/send_appointment', methods=['POST'])
@verify_args
def send_appointment(args, form):
    contract_id = args.get('contract_id')

    medsenger_api.send_message(contract_id, 'Вам необходимо запланировать онлайн-встречу с врачом. ' +
                               'Для этого воспользуйтесь кнопкой:',
                               action_name='Выбрать время', action_link='appointment', action_big=False,
                               only_patient=True, action_onetime=True)
    medsenger_api.send_message(contract_id, 'Пациенту отправлена ссылка на выбор времени консультации.',
                               only_doctor=True)
    return 'ok'


@app.route('/save_appointment', methods=['POST'])
@verify_args
def save_appointment(args, form):
    contract_id = args.get('contract_id')
    slot = request.json
    timeslot, is_new = timetable_manager.add(slot)

    patient_info = medsenger_api.get_patient_info(contract_id)
    patient_datetime = datetime.utcfromtimestamp(slot['timestamp']) - timedelta(minutes=patient_info.get('timezone_offset', -180))
    doctor_datetime = datetime.utcfromtimestamp(slot['timestamp']) - timedelta(minutes=patient_info.get('doctor_timezone_offset', -180))

    medsenger_api.send_message(contract_id,
                               'Онлайн-встреча с врачом запланирована на {} по Вашему часовому поясу. '.format(patient_datetime.strftime('%d.%m в %H:%M')) +
                               'За 10 минут до назначенного времени Вам придет сообщение с информацией для подключения.',
                               only_patient=True)
    medsenger_api.send_message(contract_id,
                               'Онлайн-встреча с пациентом запланирована на {} по Вашему часовому поясу. '.format(doctor_datetime.strftime('%d.%m в %H:%M')) +
                               'За 10 минут до назначенного времени Вам придет сообщение с информацией для подключения.',
                               only_doctor=True)

    return jsonify(timeslot.as_dict())


@app.route('/check/<call_id>', methods=['GET'])
def check_call(call_id):
    return jsonify({
        'status': 'active' if call_manager.check_call(call_id) else 'ended'
    })


@app.route('/get_call_url', methods=['GET'])
@verify_args
def create_call(args, form):
    contract_id = args.get('contract_id')

    links = call_manager.start_call(contract_id)
    return jsonify(links)


@app.route('/start_call_now', methods=['POST'])
@verify_args
def start_call(args, form):
    contract_id = request.json.get('contract_id')
    timeslot_id = request.json.get('timeslot_id', None)

    links = call_manager.start_call(contract_id, timeslot_id)
    return jsonify(links)


@app.route('/cancel_call', methods=['POST'])
@verify_args
def cancel_call(args, form):
    contract_id = request.json.get('contract_id')
    timeslot = request.json

    timetable_manager.cancel(timeslot['id'])

    medsenger_api.send_message(contract_id,
                               'Онлайн-встреча с врачом ({}) отменена.'.format(timeslot['time']),
                               only_patient=True)
    medsenger_api.send_message(contract_id,
                               'Онлайн-встреча с пациентом ({}) отменена.'.format(timeslot['time']),
                               only_doctor=True)

    return 'ok'


@app.route('/close', methods=['GET'])
def close():
    return render_template('close.html')


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(HOST, PORT, debug=API_DEBUG)
