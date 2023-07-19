from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# models
class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    agent_token = db.Column(db.String(255), nullable=True)
    engine = db.Column(db.String(255), nullable=True, server_default='zoom')
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
    created = db.Column(db.DateTime(), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id', ondelete="CASCADE"), nullable=True)

    def as_dict(self):
        return {
            'id': self.id,
            'created': self.created.timestamp(),
            'had_connection': self.had_connection,
            'contract_id': self.contract_id
        }
