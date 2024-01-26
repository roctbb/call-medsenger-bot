from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# models
class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    agent_token = db.Column(db.String(255), nullable=True)
    engine = db.Column(db.String(255), nullable=True, server_default='vc')
    show_timetable = db.Column(db.Boolean, default=False)

    def as_dict(self, native=False):
        serialized = {
            "id": self.id,
            "clinic_id": self.id,
            "is_active": self.is_active,
            "engine": self.engine,
            "show_timetable": self.show_timetable
        }

        if native:
            serialized['agent_token'] = self.agent_token

        return serialized


class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime(), nullable=False)
    status = db.Column(db.Text, nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'timestamp': self.date.timestamp(),
            'status': self.status,
            'doctor_id': self.doctor_id,
            'patient_id': self.patient_id,
            'contract_id': self.contract_id,
        }


class Call(db.Model):
    key = db.Column(db.String, primary_key=True)
    number = db.Column(db.String, nullable=True)

    def as_dict(self):
        return {
            'key': self.key,
            'number': self.number
        }


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    had_connection = db.Column(db.Boolean, nullable=True, default=False)
    connected = db.Column(db.DateTime(), nullable=True)
    duration = db.Column(db.Integer, nullable=True)

    created = db.Column(db.DateTime(), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'created': self.created.timestamp(),
            'had_connection': self.had_connection,
            'contract_id': self.contract_id,
            'connected_timestamp': self.connected.timestamp() if self.connected else self.created.timestamp(),
            'duration': self.duration
        }


class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    session_duration = db.Column(db.Integer, nullable=True, default=30)

    day_start_time = db.Column(db.String(5), nullable=True)
    day_end_time = db.Column(db.String(5), nullable=True)

    timeslot_offset = db.Column(db.Integer, nullable=True, default=30)

    def as_dict(self):
        return {
            'id': self.id,
            'duration': self.session_duration,
            'offset': self.timeslot_offset,
            'start_time': self.day_start_time,
            'end_time': self.day_end_time
        }

