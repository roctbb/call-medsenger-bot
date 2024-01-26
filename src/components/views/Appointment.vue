<template>
    <div>
        <h5>Запись на онлайн-консультацию</h5>

        <div class="row">
            <div><b>Врач:</b></div>
            <div class="col" v-if="current_doctor_id">{{ doctor.name }}</div>
            <div class="col" v-else>
                <select class="form-control form-control-sm" @change="change_doctor()"
                        v-model="doctor">
                    <option :value="d" v-for="d in patient.doctors">{{ d.name }} ({{ d.role }})</option>
                </select>
            </div>
        </div>

        <error-block :errors="errors" v-if="!days.length"/>
        <div v-else>
            Пожалуйста, выберите удобное для звонка время. После этого необходимо подтвердить свой выбор.
            <br>
            <span class="text-muted">* Время указано в Вашем часовом поясе</span>
            <br>

            <button class="btn btn-success" style="margin-top: 10px" :disabled="!chosen_slot" @click="save()">Выбрать
                <span v-if="chosen_slot">{{ chosen_slot.date }}, {{ chosen_slot.time }}</span>
            </button>

            <div v-for="(day, i) in days" style="margin-left: 5px">
                <h5>{{ day.date }}, {{ day.weekday }}</h5>
                <div class="row">
                    <button :class="btn_style(slot)" @click="choose_slot(slot)" v-for="(slot,j) in day.slots">{{
                            slot.time
                        }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import * as moment from "moment/moment";
import ErrorBlock from "../parts/ErrorBlock.vue";

export default {
    name: "Appointment",
    components: {ErrorBlock},
    props: {
        patient: {
            required: true
        }
    },
    data: function () {
        return {
            state: 'timetable',
            loaded: false,
            errors: [],
            days: [],
            doctor: undefined,
            chosen_slot: undefined
        }
    },
    methods: {
        load_timetable: function () {
            this.days = []
            this.chosen_slot = undefined
            let action = '/api/settings/get_doctor_timetable/' + this.doctor.id

            this.axios.get(this.url(action)).then((response) => {
                response.data = response.data.filter((s) => s.timestamp < this.patient.end_timestamp)
                if (!response.data.length) this.errors = ['К сожалению, у врача нет доступных для записи слотов.']
                let duration = this.patient.clinic_info ? this.patient.clinic_info.duration : 30

                let slots = response.data.sort((a, b) => a.timestamp - b.timestamp)
                slots.forEach((slot, i) => {
                    if (slot.status === 'scheduled') {
                        let index = i + 1

                        while (slots.length > index && slots[index].timestamp < slot.timestamp + duration * 60) {
                            slots[index].status = 'unavailable'
                            index++
                        }
                    }
                })

                slots = slots.filter(slot => slot.status === 'available' && slot.timestamp > moment().unix())

                let current_day_index = -1

                slots.forEach(slot => {
                    let time = moment.unix(slot.timestamp)
                    if (current_day_index < 0 || this.days[current_day_index].date !== time.format('DD.MM')) {
                        current_day_index += 1
                        this.days.push({
                            date: time.format('DD.MM'),
                            weekday: this.weekdays[time.weekday() === 0 ? 6 : time.weekday() - 1].toLowerCase(),
                            slots: []
                        })
                    }
                    slot.time = time.format('HH:mm')
                    slot.date = time.format('DD.MM')
                    this.days[current_day_index].slots.push(slot)
                })
                this.$forceUpdate()
            })
        },
        btn_style: function (slot) {
            return 'btn ' + (this.chosen_slot && slot.id === this.chosen_slot.id ? 'btn-primary' : 'btn-secondary')
        },
        choose_slot: function (slot) {
            this.chosen_slot = slot
        },
        save: function () {
            this.$confirm(
                {
                    message: `Вы уверены, что хотите подтвердить выбор (${this.chosen_slot.date}, ${this.chosen_slot.time})?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.chosen_slot.status = 'scheduled'
                            this.chosen_slot.patient_id = this.patient.id
                            this.chosen_slot.contract_id = this.current_contract_id
                            this.axios.post(this.url('/save_appointment'), this.chosen_slot).then(Event.fire('action-done'));
                        }
                    }
                })
        },
        change_doctor: function () {
            this.loaded = false
            this.load_timetable()
        }
    },
    created() {
        this.doctor = this.patient.doctors.filter((d) =>
            this.current_doctor_id && d.id == this.current_doctor_id ||
            !this.current_doctor_id && d.id == this.patient.doctor_id)[0]

        this.load_timetable()
        this.loaded = true
    }
}
</script>

<style scoped>
.row {
    margin: 5px 0;
}

</style>
