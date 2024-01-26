<template>
    <div>
        <loading v-if="!loaded"/>
        <div v-else>
            <error-block :errors="errors"/>
            <success-message :message="msg"/>

            <div class="text-center" v-if="!slots.length">
                <img :src="images.nothing_found"/>
                <h5>Нет запланированных звонков</h5>
            </div>
            <div v-else>
                <div class="row">
                    <card :class="mobile ? 'col-12' : 'col-4'" style="grid-column-gap: 0" v-for="slot in slots"
                          :key="slot.id"
                          :title="slot.time" :image="images.start_video_call">
                        <div v-if="source == 'doctor'">
                            <strong>Пациент:</strong> {{ slot.patient_name }} <br>
                            <strong>Врач:</strong> {{ slot.doctor_name }} <br><br>
                            <div v-if="current_doctor_id == slot.doctor_id">
                                <button class="btn btn-success" @click="start_call(slot)">Начать звонок</button>
                                <button class="btn btn-danger" @click="cancel_call(slot)">Отменить</button>
                            </div>
                        </div>
                        <div v-else>
                            <strong>Врач:</strong> {{ slot.doctor_name }} <br><br>
                        </div>
                    </card>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Loading from "../Loading";
import * as moment from "moment/moment";
import Card from "../parts/Card";
import ErrorBlock from "../parts/ErrorBlock";
import SuccessMessage from "../parts/SuccessMessage";

export default {
    name: "CallsList",
    components: {SuccessMessage, ErrorBlock, Card, Loading},
    props: ['source'],
    data() {
        return {
            loaded: false,
            slots: [],
            errors: [],
            msg: undefined
        }
    },
    methods: {
        load: function () {
            this.loaded = false
            let action = `/api/settings/get_${this.source}_timetable`
            if (this.source == 'doctor' && this.window_mode != 'settings') {
                action += '/' + this.current_doctor_id
            }

            this.axios.get(this.url(action)).then((response) => {
                this.slots = response.data
                    .filter(slot => slot.status == 'scheduled' && slot.timestamp >= moment().unix())
                    .sort((a, b) => a.timestamp - b.timestamp)
                this.slots.forEach(slot => {
                    slot.time = moment.unix(slot.timestamp).format('DD.MM в HH:mm')
                })
            })
            this.$forceUpdate()
            this.loaded = true
        },
        start_call: function (slot) {
            this.$confirm(
                {
                    message: `Начать звонок с пациентом (${slot.patient_name}) сейчас?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.axios.post(this.url('start_call_now'), {
                                contract_id: slot.contract_id,
                                timeslot_id: slot.id
                            }).then(response => {
                                Event.fire('action-done')
                            })
                        }
                    }
                }
            )
        },
        cancel_call: function (slot) {
            this.$confirm(
                {
                    message: `Отменить звонок с пациентом ${slot.patient_name} (${slot.time})?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.axios.post(this.url('cancel_call'), slot).then(response => {
                                slot.status = 'available'
                                this.slots = this.slots.filter(s => s.status == 'scheduled')
                                this.msg = `Онлайн-встреча с пациентом ${slot.patient_name} на ${slot.time} успешно отменена!`
                            })
                        }
                    }
                }
            )
        }

    },
    mounted() {
        this.load()
    }
}
</script>

<style scoped>
.row {
    margin: 5px -5px;
    grid-column-gap: 0;
    grid-row-gap: 5px;
}

</style>
