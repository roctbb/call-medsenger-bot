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
                             :clearable="false" :formatter="formatter" :min-date="new Date()"
                             v-model="date" @change="update"/>
            </div>
            <button class="btn btn-sm btn-primary" @click="save()">Сохранить</button>
            <button class="btn btn-sm btn-primary" @click="send()">Отправить пациенту</button>
            <button class="btn btn-sm btn-primary" @click="change_show_mode()" :disabled="flags.btn_lock">
                {{ flags.show_tt ? 'Закрыть' : 'Открыть' }}
                расписание
            </button>
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
            <br>
            <button class="btn btn-sm btn-primary" @click="change_show_mode()"
                    style="margin-top: 2px"
                    :disabled="flags.btn_lock">{{ flags.show_tt ? 'Закрыть' : 'Открыть' }}
                расписание
            </button>
        </div>

        <error-block :errors="errors"/>
        <success-message :message="msg" v-if="msg"/>

        <loading v-if="!days.length"/>
        <table class="table-bordered fixed-columns" style="font-size: smaller;">
            <colgroup>
                <col span="1" :style="`width: ${mobile ? 100 : 25}px;`">
                <col span="1" :style="col_width" v-for="i in cols_count">
            </colgroup>

            <tr>
                <td colspan="1" style="background-color: #6dc5cd"></td>
                <td class="bg-info text-light text-left" colspan="1" v-for="(day, i) in days">
                    {{ weekdays[day.weekday] }}<br>{{ day.short_date }}
                </td>
            </tr>

            <tr v-for="(time, j) in time_slots">
                <td class="align-middle font-weight-bold table-info text-center" colspan="1">{{ time }}</td>
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
                                          !expired(`${day.date} ${time}`)">+</button>
                            <button class="btn btn-link shadow-none" @click="cancel_call(day, time, i, j)"
                                    v-if="tt_slots[i][j] &&
                                          tt_slots[i][j].status === 'scheduled' && tt_slots[i][j].patient_name &&
                                          !expired(`${day.date} ${time}`)">&#215;</button>
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
import SuccessMessage from "../parts/SuccessMessage";
import axios from "axios";

export default {
    name: "Timetable",
    components: {SuccessMessage, ErrorBlock, Loading},
    props: {
        patient: {
            required: true
        }
    },
    data: function () {
        return {
            state: 'timetable',
            flags: {
                loaded: false,
                show_tt: window.PARAMS.show_tt,
                btn_lock: false
            },
            tt_settings: {
                start_time: moment('07:00', 'HH:mm'),
                end_time: moment('23:00', 'HH:mm'),
                session_duration: 30,
                session_slots_cnt: 1,
                slot_offset: 30,
                slots_cnt: 33
            },
            errors: [],
            msg: undefined,
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
            this.flags.loaded = false

            this.tt = []
            this.tt_slots = []

            for (let i = 0; i < this.cols_count; i++) {
                this.tt.push(Array(this.tt_settings.slots_cnt).fill(false))
                this.tt_slots.push(Array(this.tt_settings.slots_cnt).fill(undefined))
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
                    weekday: start.weekday() === 0 ? 6 : start.weekday() - 1,
                })
                start = start.add(1, 'day')
            }

            this.axios.get(this.url(`/api/settings/get_doctor_timetable/${date}/${this.cols_count}`))
                .then((response) => {
                    this.slots = response.data

                    this.slots.forEach(slot => {
                        let time = moment.unix(slot.timestamp)
                        slot.time = time.format('DD.MM в HH:mm')

                        let i = this.days.findIndex(d => d.date === time.format('DD.MM.YYYY'))
                        let j = this.time_slots.findIndex(t => t === time.format('HH:mm'))

                        if (this.tt_slots[i][j]) return

                        this.tt[i][j] = slot.status !== 'unavailable'

                        if (slot.status === 'scheduled') this.fill_slots(i, j)

                        this.tt_slots[i][j] = slot
                    })

                    this.$forceUpdate()

                    this.flags.loaded = true
                })
        },
        change_tt: function (mode, date, time) {
            this.msg = undefined

            let timestamp = moment(`${date.date} ${time}`, 'DD.MM.YYYY HH:mm').unix()
            let slot = this.slots.filter(s => s.timestamp === timestamp)[0]

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
                            this.msg = undefined

                            let timestamp = moment(`${day.date} ${time}`, 'DD.MM.YYYY HH:mm').unix()
                            let slot = this.slots.filter(s => s.timestamp === timestamp)[0]

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

                            this.axios.post(this.url('/save_appointment'), slot).then((response) => {
                                slot.id = response.data.id
                                this.tt_slots[i][j] = slot
                                this.msg = `${this.call_description(this.tt_slots[i][j])} успешно запланирована!`

                                this.fill_slots(i, j)

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
                            this.msg = undefined
                            this.msg = `${this.call_description(this.tt_slots[i][j])} успешно отменена!`

                            this.tt_slots[i][j].status = 'available'
                            this.tt_slots[i][j].patient_name = undefined
                            this.tt_slots[i][j].patient_id = undefined
                            this.tt_slots[i][j].contract_id = undefined
                            this.tt[i][j] = true

                            this.fill_slots(i, j, true)

                            this.$forceUpdate()
                        })
                    }
                }
            })
        },
        change_show_mode: function () {
            this.$confirm({
                message: `${this.flags.show_tt ? 'Закрыть' : 'Открыть'} самостоятельную запись для пациента ${this.patient.name}?`,
                button: {
                    no: 'Нет',
                    yes: 'Да'
                },
                callback: confirm => {
                    if (confirm) {
                        this.flags.btn_lock = true

                        if (!this.flags.show_tt) {
                            axios.post(this.url('/api/settings/show_tt_in_contract')).then((response) => {
                                this.msg = 'Расписание открыто для пациента!'
                                this.flags.show_tt = true
                                this.flags.btn_lock = false
                            })
                        } else {
                            axios.post(this.url('/api/settings/hide_tt_in_contract')).then((response) => {
                                this.msg = 'Пациент больше не может записаться самостоятельно.'
                                this.flags.show_tt = false
                                this.flags.btn_lock = false
                            })
                        }
                    }
                }
            })
        },

        expired: function (time) {
            return moment() > moment(time, 'DD.MM.YYYY HH:mm')
        },

        save: function (sent) {
            this.axios.post(this.url('/api/settings/save_doctor_timetable'), {
                slots: this.slots
            }).then(response => {
                this.msg = `Расписание успешно сохранено ${sent ? 'и отправлено пациенту' : ''}!`
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
            if (timeslot && timeslot.status === 'available') color = '#e9f6f7'
            if (timeslot && ['scheduled', 'finished'].includes(timeslot.status)) color = '#d1edef'
            if (this.expired(dt)) color = '#f8f8f8'
            return 'background-color: ' + color
        },
        call_description: function (slot) {
            return `Онлайн-встреча с пациентом <b>${slot.patient_name} на ${slot.time}</b>`
        },
        fill_slots: function (slot_day_index, slot_index, cancel) {
            let max_cnt = Math.min(this.tt_settings.slots_cnt, slot_index + this.tt_settings.session_slots_cnt)
            for (let index = slot_index + 1; index < max_cnt; index++) {
                if (cancel) {
                    if (this.tt_slots[slot_day_index][index].old_status)
                        this.tt_slots[slot_day_index][index].status = this.tt_slots[slot_day_index][index].old_status
                    else this.tt_slots[slot_day_index][index] = undefined
                    continue
                }
                if (!this.tt_slots[slot_day_index][index]) this.tt_slots[slot_day_index][index] = {}
                else this.tt_slots[slot_day_index][index].old_status = this.tt_slots[slot_day_index][index].status

                this.tt_slots[slot_day_index][index].status = 'scheduled'
            }
        }
    },
    computed: {
        time_slots() {
            let slots = []
            let time = this.tt_settings.start_time

            while (slots.length < this.tt_settings.slots_cnt) {
                slots.push(time.format('HH:mm'))
                time = time.add(this.tt_settings.slot_offset, 'minutes')
            }
            return slots
        },
        col_width: function () {
            let w = Math.floor((window.innerWidth * 0.9 - (this.mobile ? 100 : 25)) / this.cols_count)
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

        if (this.patient.clinic_info) {
            this.tt_settings = {
                start_time: moment(this.patient.clinic_info.start_time, 'HH:mm'),
                end_time: moment(this.patient.clinic_info.end_time, 'HH:mm'),
                session_duration: this.patient.clinic_info.duration,
                session_slots_cnt: undefined,
                slot_offset: this.patient.clinic_info.offset,
                slots_cnt: undefined
            }
            this.tt_settings.slots_cnt = Math.ceil(this.tt_settings.end_time.diff(this.tt_settings.start_time, 'minutes') / this.tt_settings.slot_offset) + 1
            this.tt_settings.session_slots_cnt = Math.ceil(this.tt_settings.session_duration / this.tt_settings.slot_offset)
        }

        this.load_timetable()
        Event.listen('dashboard-to-main', () => {
            if (window.MODE === 'settings') {
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
