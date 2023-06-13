<template>
    <div>
        <loading v-if="!days.length"/>
        <error-block :errors="errors"/>
        <table class="table table-bordered fixed-columns" :style="text_size">
            <colgroup>
                <col span="1" style="width: 9%;">
                <col span="1" style="width: 13%;" v-for="i in 7">
            </colgroup>

            <tr>
                <td class="bg-info text-light align-middle" colspan="1">Время</td>
                <td class="bg-info text-light align-middle" colspan="1" v-for="(day, i) in days">
                    {{ mobile ? short_weekdays[day.weekday] : weekdays[day.weekday] }}<br>{{ day.short_date }}
                </td>
            </tr>

            <tr v-for="(time, j) in time_slots">
                <td class="align-middle font-weight-bold table-info" colspan="1">{{ time }}</td>
                <td class="align-middle" colspan="1" v-for="(day, i) in days"
                    :style="expired(`${day.date} ${time}`) ? 'background-color: #EEE' : ''">
                    <div v-if="tt_slots[i][j] && ['scheduled', 'finished'].includes(tt_slots[i][j].status)">
                        <img :src="tt_slots[i][j].patient_sex == 'male' ? images.male_patient : images.female_patient"
                             height="35" :title="tt_slots[i][j].patient_name"
                             v-if="tt_slots[i][j].status == 'scheduled'">
                        <img
                            :src="tt_slots[i][j].patient_sex == 'male' ? images.finished_male_patient : images.finished_female_patient"
                            height="35" :title="tt_slots[i][j].patient_name + ' (завершен)'"
                            v-else-if="tt_slots[i][j].status == 'finished'">
                    </div>
                    <input type="checkbox" :disabled="expired(`${day.date} ${time}`)"
                           @change="change_tt(tt[i][j], day, time)" v-model="tt[i][j]" v-else/>
                </td>
            </tr>

        </table>
    </div>
</template>

<script>
import * as moment from "moment/moment";
import Loading from "../Loading";
import axios from "axios";
import ErrorBlock from "../parts/ErrorBlock";

export default {
    name: "Timetable",
    components: {ErrorBlock, Loading},
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
            slots: [],
            tt: [],
            tt_slots: []
        }
    },
    methods: {
        load_timetable: function (start) {
            this.loaded = false
            this.tt = []
            for (let i = 0; i < 7; i++) {
                this.tt.push(Array(2 * 16 + 1).fill(false))
                this.tt_slots.push(Array(2 * 16 + 1).fill(undefined))
            }


            if (!start) start = moment()
            start = start.startOf('day')

            this.days = []
            while (this.days.length < 7) {
                this.days.push({
                    start_of_day: start,
                    date: start.format('DD.MM.YYYY'),
                    short_date: start.format('DD.MM'),
                    weekday: start.weekday() == 0 ? 6 : start.weekday() - 1,
                })
                start = start.add(1, 'day')
            }
            this.axios.get(this.url('/api/settings/get_doctor_timetable')).then((response) => {
                this.slots = response.data
                this.slots.forEach(slot => {
                    let time = moment.unix(slot.timestamp)
                    let i = this.days.findIndex(d => d.date == time.format('DD.MM.YYYY'))
                    let j = this.time_slots.findIndex(t => t == time.format('HH:mm'))
                    this.tt[i][j] = slot.status != 'unavailable'
                    this.tt_slots[i][j] = slot
                })
                this.$forceUpdate()
            })
            this.loaded = true
        },
        change_tt: function (mode, date, time) {
            let timestamp = moment(`${date.date} ${time}`, 'DD.MM.YYYY HH:mm').unix()
            let slot = this.slots.filter(s => s.timestamp == timestamp)[0]

            if (slot) {
                slot.status = mode ? 'available' : 'unavailable'
            } else {
                this.slots.push({
                    status: mode ? 'available' : 'unavailable',
                    timestamp: timestamp,
                    doctor_id: this.patient.doctor_id,
                })
            }
        },

        expired: function (time) {
            return moment() > moment(time, 'DD.MM.YYYY HH:mm')
        }
    },
    computed: {
        text_size: function () {
            return this.mobile ? 'font-size: smaller;' : ''
        },
        time_slots: function () {
            let slots = []
            let time = moment('07:00', 'HH:mm')

            while (slots.length < 2 * 16 + 1) {
                slots.push(time.format('HH:mm'))
                time = time.add(30, 'minutes')
            }

            return slots
        },
    },
    created() {
    },
    mounted() {
        this.load_timetable()
        Event.listen('dashboard-to-main', () => {
            if (window.MODE == 'settings') {
                this.state = 'main'
            }
        });

        Event.listen('home', () => {
            this.state = 'main'
        });

        Event.listen('back-to-dashboard', () => {
        })

        Event.listen('save-doctor-slots', () => {
            this.axios.post(this.url('/api/settings/save_doctor_timetable'), {
                slots: this.slots
            }).then(response => {
                this.errors = [`Расписание сохранено! (${moment().format('HH:mm')})`]
                this.slots = response.data
            });
        })
    }

}
</script>

<style scoped>
input[type="checkbox"] {
    width: 1.2em;
    height: 1.2em;
    border-radius: 0.15em;
    transform: translateY(-0.075em);
    accent-color: #2ab6c2;
}

.table {
    width: 100%;
    text-align: center;
}

table tr {
    break-inside: avoid;
}

</style>
