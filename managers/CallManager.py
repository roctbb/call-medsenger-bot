from threading import Thread

import vc_api
import zoom_api
from helpers import log, get_sign
from managers.Manager import Manager
from managers.ContractsManager import ContractManager
from models import Contract, TimeSlot, Call, Room
from config import *
from datetime import datetime, timedelta
import time


class CallManager(Manager):
    def __init__(self, contracts_manager: ContractManager, *args):
        super(CallManager, self).__init__(*args)
        self.contracts_manager = contracts_manager

    def add_call(self, call_info):
        call = Call.query.filter_by(key=call_info.get('key', '')).first()
        is_new = False
        if not call:
            is_new = True
            call = Call(key=call_info['key'])
            self.db.session.add(call)

        call.number = call_info['number']
        self.__commit__()

        return call, is_new

    def get_call(self, key):
        call = Call.query.filter_by(key=key).first()

        if not call:
            raise Exception("No key = {} found".format(key))

        return call

    def add_room(self, room_info):
        room = Room.query.filter_by(id=room_info.get('id', '')).first()
        is_new = False
        if not room:
            is_new = True
            room = Room(id=room_info['id'])
            self.db.session.add(room)

        room.created = datetime.now()
        room.contract_id = room_info['contract_id']
        room.state = 'OPENED'
        self.__commit__()

        return room, is_new

    def get_room(self, room_id):
        room = Room.query.filter_by(id=room_id).first()

        if not room:
            raise Exception("No id = {} found".format(room_id))

        return room

    def update_room_state(self, room_id):
        try:
            room = Contract.query.filter_by(id=room_id).first()

            if not room:
                raise Exception("No room_id = {} found".format(room_id))

            room.had_connection = True

            self.__commit__()
        except Exception as e:
            log(e)

    def create_zoom_call(self, patient_info):
        key = patient_info.get('doctor_zoom_key')
        sec = patient_info.get('doctor_zoom_sec')

        if not key or not sec:
            key, sec = DEFAULT_ACCOUNT
            # return "Видеозвонки не настроены."

        try:
            call = self.get_call(key)
            zoom_api.endMeeting(key, sec, call.number)
            call.number = None
            log('call {} ended successfully'.format(call.number))
            self.__commit__()
        except Exception as e:
            call, is_new = self.add_call({
                'key': key,
                'number': None,
            })
            pass

        number, password, host_key, join_url = zoom_api.createMeeting(key, sec)
        call.number = number
        self.__commit__()
        return number, password, host_key, join_url, join_url

    def check_call(self, call_id):
        call = Call.query.filter_by(number=call_id).first()
        return call is not None

    def start_call(self, contract_id, timeslot_id=None):
        info = self.medsenger_api.get_patient_info(contract_id)
        contract = self.contracts_manager.get(contract_id)

        if contract.engine == 'zoom':
            number, password, host_key, join_url, join_url = self.create_zoom_call(info)
            call_url = "{}/{}/{}".format(LOCALHOST, number, password)

            self.medsenger_api.send_message(contract_id, 'Видеозвонок от врача.', action_link=call_url,
                                            action_type='zoom', action_name='Подключиться к конференции',
                                            send_from='doctor', action_deadline=int(time.time() + 60 * 25))

            if timeslot_id:
                timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()
                timeslot.status = 'finished'
                self.__commit__()

            return {
                       "join_url": join_url,
                       "call_url": call_url
                   },
        else:
            room_id, doctor_link, patient_link = vc_api.createMeeting()
            self.add_room({
                "id": room_id,
                "contract_id": contract_id
            })

            self.medsenger_api.send_message(contract_id, 'Видеозвонок c пациентом.', action_link=doctor_link,
                                            action_type='url', action_name='Подключиться к конференции',
                                            only_doctor=True, action_deadline=int(time.time() + 60 * 40))

            self.medsenger_api.send_message(contract_id, 'Видеозвонок от врача.', action_link=patient_link,
                                            action_type='url', action_name='Подключиться к конференции',
                                            only_patient=True, action_deadline=int(time.time() + 60 * 40))

            if timeslot_id:
                timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()
                timeslot.status = 'finished'
                self.__commit__()

            return {
                "vc_doctor_link": doctor_link,
                "vc_patient_link": patient_link
            }

    def get_report(self, clinic_id, date_from, date_to):
        date_from = datetime.fromtimestamp(date_from)
        date_to = datetime.fromtimestamp(date_to)
        contracts = self.contracts_manager.get_clinic_contracts(clinic_id)
        meetings_held = Room.query.filter(Room.contract_id.in_(contracts),
                                          Room.created >= date_from,
                                          Room.created <= date_to,
                                          Room.had_connection).all()
        return len(meetings_held)

    def iterate(self, app):
        with app.app_context():
            notification_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=10)
            call_time = datetime.now().replace(second=0, microsecond=0)
            timeslots = TimeSlot.query.filter_by(date=notification_time, status='scheduled').all()
            timeslots += TimeSlot.query.filter_by(date=call_time, status='scheduled').all()
            for timeslot in timeslots:
                if timeslot.date == call_time:
                    self.start_call(timeslot.contract_id, timeslot.id)
                elif timeslot.date == notification_time:
                    self.medsenger_api.send_message(timeslot.contract_id,
                                                    'Запланированный видеозвонок начнется через 10 минут.',
                                                    action_deadline=int(time.time() + 60 * 30))

    def check_rooms(self, app):
        with app.app_context():
            notification_time = datetime.now() - timedelta(minutes=45)
            room_ids = [room.as_dict()['id'] for room in Room.query.filter(Room.created >= notification_time,
                                                                           Room.had_connection.is_(False)).all()]
            for room_id in room_ids:
                info = vc_api.getMeetingInfo(room_id)
                if info.get('had_connection'):
                    self.update_room_state(room_id)
