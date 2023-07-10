<template>
    <div>
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
</template>

<script>
import * as moment from "moment/moment";

export default {
    name: "Appointment",
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
            chosen_slot: undefined
        }
    },
    methods: {
        load_timetable: function () {
            this.axios.get(this.url('/api/settings/get_doctor_timetable')).then((response) => {
                if (!response.data.length) this.errors = ['К сожалению, у врача нет доступных для записи слотов.']
                let slots = response.data
                    .filter(slot => slot.status == 'available' && slot.timestamp > moment().unix())
                    .sort((a, b) => a.timestamp - b.timestamp)
                let current_day_index = -1
                slots.forEach(slot => {
                    let time = moment.unix(slot.timestamp)
                    if (current_day_index < 0 || this.days[current_day_index].date != time.format('DD.MM')) {
                        current_day_index += 1
                        this.days.push({
                            date: time.format('DD.MM'),
                            weekday: this.weekdays[time.weekday() == 0 ? 6 : time.weekday() - 1].toLowerCase(),
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
            return 'btn ' + (this.chosen_slot && slot.id == this.chosen_slot.id ? 'btn-primary' : 'btn-secondary')
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
                }
            )

        }
    },
    created() {
        this.load_timetable()
        this.loaded = true
    }
}
</script>

<style scoped>

</style>
