from helpers import log, get_patient_data
from sqlalchemy import and_
from managers.Manager import Manager
from models import TimeSlot
from datetime import datetime, timedelta


class TimetableManager(Manager):
    def __init__(self, *args):
        super(TimetableManager, self).__init__(*args)

    def add(self, timeslot_info):
        timeslot_id = timeslot_info.get('id')
        if timeslot_id:
            timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()
        else:
            timeslot = TimeSlot.query.filter_by(date=datetime.fromtimestamp(timeslot_info['timestamp']),
                                                doctor_id=timeslot_info['doctor_id']).first()
        is_new = False
        if not timeslot:
            if timeslot_info['status'] == 'unavailable':
                return None, None
            is_new = True
            timeslot = TimeSlot(date=datetime.fromtimestamp(timeslot_info['timestamp']),
                                doctor_id=timeslot_info['doctor_id'])
            self.db.session.add(timeslot)

        timeslot.status = timeslot_info['status']
        if timeslot_info['status'] == 'scheduled':
            timeslot.patient_id = timeslot_info.get('patient_id')
            timeslot.contract_id = timeslot_info.get('contract_id')
        self.__commit__()

        return timeslot, is_new

    def remove(self, timeslot_id):
        try:
            timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

            if not timeslot:
                raise Exception("No timeslot_id = {} found".format(timeslot_id))

            timeslot.status = 'unavailable'

            self.__commit__()
        except Exception as e:
            log(e)

    def cancel(self, timeslot_id):
        try:
            timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

            if not timeslot:
                raise Exception("No timeslot_id = {} found".format(timeslot_id))

            timeslot.status = 'available'

            timeslot.patient_id = None
            timeslot.contract_id = None

            self.__commit__()
        except Exception as e:
            log(e)

    def get_patient_timetable(self, patient_id):
        timeslots = TimeSlot.query.filter_by(patient_id=patient_id).all()
        start_of_day = datetime.now()
        timeslots = [timeslot.as_dict() for timeslot in timeslots if timeslot.date >= start_of_day]
        for timeslot in timeslots:
            info =get_patient_data(timeslot['contract_id'])
            doctor = list(filter(lambda d: d['id'] == int(timeslot['doctor_id']), info['doctors']))[0]
            timeslot['doctor_name'] = doctor['name']
        return timeslots

    def get_doctor_timetable(self, doctor_id):
        timeslots = TimeSlot.query.filter(TimeSlot.doctor_id == doctor_id,
                                          TimeSlot.date >= datetime.now()).all()
        timeslots = self.process_timeslots(timeslots)
        return timeslots

    def get_contract_timetable(self, contract_id):
        timeslots = TimeSlot.query.filter(TimeSlot.contract_id == contract_id,
                                          TimeSlot.date >= datetime.now()).all()
        timeslots = self.process_timeslots(timeslots)
        return timeslots

    def get_doctor_period_timetable(self, doctor_id, date, days):
        start = datetime.fromtimestamp(date)
        end = datetime.fromtimestamp(date) + timedelta(days=days)
        timeslots = TimeSlot.query.filter(TimeSlot.doctor_id == doctor_id,
                                          TimeSlot.date >= start, TimeSlot.date <= end).all()
        timeslots = self.process_timeslots(timeslots)

        return timeslots

    def process_timeslots(self, timeslots):
        timeslots = [timeslot.as_dict() for timeslot in timeslots]

        for timeslot in timeslots:
            if timeslot['contract_id']:
                info = get_patient_data(timeslot['contract_id'])
                name_parts = list(filter(lambda x:bool(x), info['name'].split(' ')))
                if name_parts:
                    timeslot['patient_name'] = name_parts[0]
                    if len(name_parts) > 1:
                        timeslot['patient_name'] += ' {}.'.format(name_parts[1][0])
                    if len(name_parts) > 2:
                        timeslot['patient_name'] += ' {}.'.format(name_parts[2][0])
                else:
                    timeslot['patient_name'] = ''
                timeslot['patient_sex'] = info['sex']
                doctor = list(filter(lambda d: d['id'] == int(timeslot['doctor_id']), info['doctors']))[0]
                timeslot['doctor_name'] = doctor['name']

        return timeslots

    def get(self, timeslot_id):
        timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

        if not timeslot:
            raise Exception("No timeslot_id = {} found".format(timeslot_id))

        return timeslot
