from helpers import log
from managers.Manager import Manager
from models import TimeSlot
from datetime import datetime


class TimetableManager(Manager):
    def __init__(self, *args):
        super(TimetableManager, self).__init__(*args)

    def add(self, timeslot_info):
        timeslot = TimeSlot.query.filter_by(id=timeslot_info.get('id')).first()
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
            info = self.medsenger_api.get_patient_info(timeslot['contract_id'])
            timeslot['doctor_name'] = info['doctor_name']
        return timeslots

    def get_doctor_timetable(self, doctor_id):
        timeslots = TimeSlot.query.filter_by(doctor_id=doctor_id).all()
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        timeslots = [timeslot.as_dict() for timeslot in timeslots if timeslot.date >= start_of_day]
        for timeslot in timeslots:
            if timeslot['contract_id']:
                info = self.medsenger_api.get_patient_info(timeslot['contract_id'])
                timeslot['patient_name'] = info['name']
                timeslot['patient_sex'] = info['sex']
        return timeslots

    def get(self, timeslot_id):
        timeslot = TimeSlot.query.filter_by(id=timeslot_id).first()

        if not timeslot:
            raise Exception("No timeslot_id = {} found".format(timeslot_id))

        return timeslot
