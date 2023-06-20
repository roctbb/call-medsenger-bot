<template>
    <div>
        <div class="row align-items-center"
             style="margin: 5px 0" v-if="!mobile">
            <div class="col" style="padding: 0">
                Пожалуйста, отметьте удобное для Вас время
            </div>
            <div>
                <date-picker type="week" value-type="timestamp" style="width: 230px"
                             :clearable="false" :formatter="formatter"
                             v-model="date" @change="update"/>
            </div>
            <button class="btn btn-sm btn-primary" @click="save()">Сохранить</button>
            <button class="btn btn-sm btn-primary" @click="send()">Отправить пациенту</button>
        </div>
        <div style="margin: 5px 0" v-else>
            <div style="padding: 0">
                Пожалуйста, отметьте удобное для Вас время
            </div>
            <div style="margin: 5px 0;">
                <date-picker type="week" value-type="timestamp" style="width: 230px"
                             :clearable="false" :formatter="formatter"
                             v-model="date" @change="update"/>
            </div>
            <button class="btn btn-sm btn-primary" @click="save()">Сохранить</button>
            <button class="btn btn-sm btn-primary" @click="send()">Отправить пациенту</button>
        </div>

        <error-block :errors="errors"/>
        <loading v-if="!days.length"/>
        <table class="table-bordered fixed-columns" style="font-size: smaller;">
            <colgroup>
                <col span="1" style="width: 25px;">
                <col span="1" :style="col_width" v-for="i in 7">
            </colgroup>

            <tr>
                <td colspan="1" style="background-color: #6dc5cd"></td>
                <td class="bg-info text-light text-left" colspan="1" v-for="(day, i) in days">
                    {{ mobile ? short_weekdays[day.weekday] : weekdays[day.weekday] }}<br>{{ day.short_date }}
                </td>
            </tr>

            <tr v-for="(time, j) in time_slots">
                <td class="align-middle font-weight-bold table-info" colspan="1">{{ time }}</td>
                <td class="align-middle" colspan="1" v-for="(day, i) in days"
                    :style="cell_bg(`${day.date} ${time}`, tt_slots[i][j])">
                    <div v-if="tt_slots[i][j] && ['scheduled', 'finished'].includes(tt_slots[i][j].status)"
                         style="font-size: small; text-align: left">
                        {{ tt_slots[i][j].patient_name }}
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
            tt_slots: [],
            date: undefined,
            formatter: {
                //[optional] Date to String
                stringify: (date) => {
                    let start = moment(date).startOf('week').add(1, 'day')
                    let end = moment(date).endOf('week').add(1, 'day')
                    return date ? ('c ' + start.format('DD.MM.YYYY') + ' по ' + end.format('DD.MM.YYYY')) : ''
                },
                //[optional]  String to Date
                parse: (value) => {
                    return value ? moment(value.split(' по ', 'с ')[0], 'DD.MM.YYYY').toDate() : null
                },
                //[optional] getWeekNumber
                getWeek: (date) => {
                    return //date ? moment(date).format('gg') : 0
                }
            }
        }
    },
    methods: {
        load_timetable: function () {
            this.loaded = false
            this.tt = []
            this.tt_slots = []
            for (let i = 0; i < 7; i++) {
                this.tt.push(Array(2 * 16 + 1).fill(false))
                this.tt_slots.push(Array(2 * 16 + 1).fill(undefined))
            }

            let date = moment(this.date).startOf('week').add(1, 'day').unix()
            let start = moment(this.date).startOf('week').add(1, 'day')

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

            this.axios.get(this.url('/api/settings/get_doctor_timetable/' + date))
                .then((response) => {
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
        },

        save: function () {
            this.axios.post(this.url('/api/settings/save_doctor_timetable'), {
                slots: this.slots
            }).then(response => {
                this.errors = [`Расписание сохранено! (${moment().format('HH:mm')})`]
                this.slots = response.data
            });
        },
        send: function () {
            this.$confirm({
                    message: `Сохранить и отправить расписание?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.save()
                            this.axios.post(this.url('/send_appointment')).then(Event.fire('action-done'));
                        }
                    }
                }
            )
        },
        update: function () {
            this.load_timetable()
        },
        cell_bg: function (dt, timeslot) {
            let color = 'transparent'
            if (timeslot && timeslot.status == 'available') color = '#e9f6f7'
            if (timeslot && ['scheduled', 'finished'].includes(timeslot.status)) color = '#d1edef'
            if (this.expired(dt)) color = '#f8f8f8'
            return 'background-color: ' + color
        }
    },
    computed: {
        time_slots: function () {
            let slots = []
            let time = moment('07:00', 'HH:mm')

            while (slots.length < 2 * 16 + 1) {
                slots.push(time.format('HH:mm'))
                time = time.add(30, 'minutes')
            }

            return slots
        },
        col_width: function () {
            let w = Math.floor((window.innerWidth * 0.9 - 25) / 7)
            return 'width: ' + w + 'px;'
        }
    },
    created() {
    },
    mounted() {
        this.date = moment().startOf('week').add(1, 'day').unix() * 1000
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
    margin: 5px;
}

table {
    width: 100%;
    text-align: center;
}

table tr {
    break-inside: avoid;
}

table td {
    padding: 2px 7px;
}

.btn-sm {
    height: 34px;
}

.bg-info {
    background-color: #25a8b4;
}

.table-info {
    background-color: #f8f8f8;
}

th, td {
    border-color: #D3D3D3;
}
</style>
