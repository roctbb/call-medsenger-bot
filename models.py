from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# models
class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    agent_token = db.Column(db.String(255), nullable=True)
    engine = db.Column(db.String(255), nullable=True, server_default='zoom')

    def as_dict(self, native=False):
        serialized = {
            "id": self.id,
            "is_active": self.is_active,
            "engine": self.engine
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
