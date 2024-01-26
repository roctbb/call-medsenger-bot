from helpers import log, get_patient_data
from managers.Manager import Manager
from models import Contract, Clinic


class ContractManager(Manager):
    def __init__(self, *args):
        super(ContractManager, self).__init__(*args)

    def add(self, contract_id, engine=None):
        contract = Contract.query.filter_by(id=contract_id).first()
        is_new = False
        if not contract:
            is_new = True
            contract = Contract(id=contract_id)
            self.db.session.add(contract)

        contract.is_active = True

        print("Engine is:", engine)
        if engine:
            contract.engine = engine

        contract.agent_token = self.medsenger_api.get_agent_token(contract_id).get('agent_token')
        contract.clinic_id = self.medsenger_api.get_patient_info(contract_id).get('clinic_id')

        self.__commit__()

        return contract, is_new

    def remove(self, contract_id):
        try:
            contract = Contract.query.filter_by(id=contract_id).first()

            if not contract:
                raise Exception("No contract_id = {} found".format(contract_id))

            contract.is_active = False

            self.__commit__()
        except Exception as e:
            log(e)

    def not_exists(self, contract_id):
        contract = Contract.query.filter_by(id=contract_id).first()

        if contract and not contract.clinic_id:
            contract.clinic_id = self.medsenger_api.get_patient_info(contract_id).get('clinic_id')
            self.__commit__()

        return not contract

    def get_patient(self, contract_id):
        contract = Contract.query.filter_by(id=contract_id).first()

        if not contract:
            raise Exception("No contract_id = {} found".format(contract_id))

        patient_info = get_patient_data(contract_id)

        clinic = Clinic.query.filter_by(id=contract.clinic_id).first()
        if clinic:
            patient_info.update({
                "clinic_info": clinic.as_dict()
            })

        return patient_info

    def change_show_tt_mode(self, contract_id, show_tt):
        contract = Contract.query.filter_by(id=contract_id).first()
        contract.show_timetable = show_tt
        self.__commit__()
        return 'ok'

    def get(self, contract_id):
        contract = Contract.query.filter_by(id=contract_id).first()

        if not contract:
            raise Exception("No contract_id = {} found".format(contract_id))

        return contract

    def get_active_ids(self):
        return [contract.id for contract in Contract.query.filter_by(is_active=True).all()]

    def get_clinic_contracts(self, clinic_id):
        return [contract.id for contract in Contract.query.filter_by(clinic_id=clinic_id).all()]
