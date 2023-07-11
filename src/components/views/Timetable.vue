<template>
    <div>
        <div class="row align-items-center"
             style="margin: 5px 0" v-if="!mobile">
            <div class="col" style="padding: 0">
                Пожалуйста, отметьте удобное для Вас время
                <br>
                <span class="text-muted">* Время указано в Вашем часовом поясе</span>
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
                <br>
                <span class="text-muted">* Время указано в Вашем часовом поясе</span>
            </div>
            <div style="margin: 5px 0;">
                <date-picker type="day" value-type="timestamp" style="width: 100%"
                             format="DD.MM.YYYY"
                             :clearable="false" v-model="date" @change="update"/>
            </div>
            <button class="btn btn-sm btn-primary" @click="save()">Сохранить</button>
            <button class="btn btn-sm btn-primary" @click="send()">Отправить пациенту</button>
        </div>

        <error-block :errors="errors"/>
        <loading v-if="!days.length"/>
        <table class="table-bordered fixed-columns" style="font-size: smaller;">
            <colgroup>
                <col span="1" style="width: 25px;">
                <col span="1" :style="col_width" v-for="i in cols_count">
            </colgroup>

            <tr>
                <td colspan="1" style="background-color: #6dc5cd"></td>
                <td class="bg-info text-light text-left" colspan="1" v-for="(day, i) in days">
                    {{ weekdays[day.weekday] }}<br>{{ day.short_date }}
                </td>
            </tr>

            <tr v-for="(time, j) in time_slots">
                <td class="align-middle font-weight-bold table-info" colspan="1">{{ time }}</td>
                <td colspan="1" v-for="(day, i) in days"
                    :style="cell_bg(`${day.date} ${time}`, tt_slots[i][j], tt[i][j])">
                    <div class="row" style="margin: 0">
                        <div v-if="tt_slots[i][j] && ['scheduled', 'finished'].includes(tt_slots[i][j].status)"
                             style="font-size: small;">
                            {{ tt_slots[i][j].patient_name }}
                        </div>
                        <div class="col align-self-start" style="padding: 0" v-else>
                            <input type="checkbox" style="margin-left: 0"
                                   :disabled="expired(`${day.date} ${time}`)" :id="`${i}_${j}`"
                                   @change="change_tt(tt[i][j], day, time)" v-model="tt[i][j]"/>
                        </div>

                        <div class="col align-self-end" style="font-size: small; text-align: right">
                            <button class="btn btn-link shadow-none" @click="add_call(day, time, i, j)"
                                    v-if="!(tt_slots[i][j] &&
                                    ['scheduled', 'finished'].includes(tt_slots[i][j].status)) &&
                                    !expired(`${day.date} ${time}`)">+
                            </button>
                            <button class="btn btn-link shadow-none" @click="cancel_call(day, time, i, j)"
                                    v-if="tt_slots[i][j] &&
                                    tt_slots[i][j].status == 'scheduled' &&
                                    !expired(`${day.date} ${time}`)">&#215;
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </div>
</template>

<script>
import * as moment from "moment/moment";
import Loading from "../Loading";
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
            for (let i = 0; i < this.cols_count; i++) {
                this.tt.push(Array(2 * 16 + 1).fill(false))
                this.tt_slots.push(Array(2 * 16 + 1).fill(undefined))
            }

            let date = !this.mobile ?
                moment(this.date).startOf('week').add(1, 'day').unix() :
                moment(this.date).startOf('day').unix()
            let start = !this.mobile ?
                moment(this.date).startOf('week').add(1, 'day') :
                moment(this.date).startOf('day')
            this.days = []
            while (this.days.length < this.cols_count) {
                this.days.push({
                    start_of_day: start,
                    date: start.format('DD.MM.YYYY'),
                    short_date: start.format('DD.MM'),
                    weekday: start.weekday() == 0 ? 6 : start.weekday() - 1,
                })
                start = start.add(1, 'day')
            }

            this.axios.get(this.url(`/api/settings/get_doctor_timetable/${date}/${this.cols_count}`))
                .then((response) => {
                    this.slots = response.data
                    this.slots.forEach(slot => {
                        let time = moment.unix(slot.timestamp)
                        slot.time = time.format('DD.MM в HH:mm')
                        let i = this.days.findIndex(d => d.date == time.format('DD.MM.YYYY'))
                        let j = this.time_slots.findIndex(t => t == time.format('HH:mm'))
                        this.tt[i][j] = slot.status != 'unavailable'
                        this.tt_slots[i][j] = slot
                    })
                    this.$forceUpdate()
                    this.loaded = true
                })
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
        add_call: function (day, time, i, j) {
            this.$confirm({
                    message: `Записать пациента ${this.patient.name} на ${day.date} в ${time}?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            let timestamp = moment(`${day.date} ${time}`, 'DD.MM.YYYY HH:mm').unix()
                            let slot = this.slots.filter(s => s.timestamp == timestamp)[0]

                            if (!slot) {
                                slot = {
                                    timestamp: timestamp,
                                    doctor_id: this.patient.doctor_id
                                }
                                this.slots.push(slot)
                            }
                            slot.status = 'scheduled'
                            slot.patient_id = this.patient.id
                            slot.contract_id = this.current_contract_id
                            slot.time = `${day.date} в ${time}`

                            let name_parts = this.patient.name.split(' ')
                            slot.patient_name = name_parts[0]
                            if (name_parts.length > 1) slot.patient_name += ` ${name_parts[1][0]}.`
                            if (name_parts.length > 2) slot.patient_name += ` ${name_parts[2][0]}.`

                            this.axios.post(this.url('/save_appointment'), slot).then(() => {
                                this.tt_slots[i][j] = slot
                                this.errors = [`Онлайн-встреча с пациентом ${this.tt_slots[i][j].patient_name} на ${this.tt_slots[i][j].time} успешно запланирована! (${moment().format('HH:mm')})`]
                                this.$forceUpdate()
                            });
                        }
                    }
                }
            )

        },
        cancel_call: function (day, time, i, j) {
            this.$confirm({
                    message: `Отменить запись пациента ${this.tt_slots[i][j].patient_name} на ${day.date} в ${time}?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.axios.post(this.url('cancel_call'), this.tt_slots[i][j]).then(response => {
                                this.tt_slots[i][j].status = 'available'
                                this.errors = [`Онлайн-встреча с пациентом ${this.tt_slots[i][j].patient_name} на ${this.tt_slots[i][j].time} успешно отменена! (${moment().format('HH:mm')})`]
                                this.tt_slots[i][j].patient_name = undefined
                                this.tt_slots[i][j].patient_id = undefined
                                this.tt_slots[i][j].contract_id = undefined
                                this.tt[i][j] = true
                                this.$forceUpdate()
                            })
                        }
                    }
                }
            )

        },

        expired: function (time) {
            return moment() > moment(time, 'DD.MM.YYYY HH:mm')
        },

        save: function (sent) {
            this.axios.post(this.url('/api/settings/save_doctor_timetable'), {
                slots: this.slots
            }).then(response => {
                this.errors = [`Расписание сохранено! (${moment().format('HH:mm')})`]
                this.slots = response.data
                if (sent) this.errors.push(`Расписание отправлено пациенту! (${moment().format('HH:mm')})`)
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
                            this.axios.post(this.url('/send_appointment')).then(() => {
                                this.save(true)
                            });
                        }
                    }
                }
            )
        },
        update: function () {
            this.load_timetable()
        },
        cell_bg: function (dt, timeslot, tt) {
            let color = tt ? '#e9f6f7' : 'transparent'
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
            let w = Math.floor((window.innerWidth * 0.9 - 25) / this.cols_count)
            return 'width: ' + w + 'px;'
        },
        cols_count: function () {
            return this.mobile ? 1 : 7
        }
    },
    created() {
    },
    mounted() {
        this.date = this.mobile ?
            moment().startOf('day').unix() * 1000 :
            moment().startOf('week').add(1, 'day').unix() * 1000
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
}

table tr {
    break-inside: avoid;
}

table td {
    padding: 2px 5px;
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

.btn-link {
    color: #25a8b4;
    height: 25px;
    padding: 0;
}
</style>
