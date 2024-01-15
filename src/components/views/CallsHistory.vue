<template>
    <div>
        <loading v-if="!loaded"/>
        <div v-else>
            <error-block :errors="errors"/>
            <success-message :message="msg"/>

            <div class="text-center" v-if="!calls.length">
                <img :src="images.nothing_found"/>
                <h5>Нет звонков</h5>
            </div>

            <div v-else>
                <card>
                    <div v-for="(call, i) in calls">
                        <div class="row">
                            <img :src="call.had_connection ? images.call : images.disconnected_call" height="25">
                            <div class="col">{{call.start_time}}</div>
                            <div class="col text-right text-muted">{{call.duration_description}}</div>
                        </div>
                        <hr v-if="i != calls.length - 1">
                    </div>
                </card>
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
import ca from "vue2-datepicker/locale/es/ca";

export default {
    name: "CallsHistory",
    components: {SuccessMessage, ErrorBlock, Card, Loading},
    props: ['source'],
    data() {
        return {
            loaded: false,
            calls: [],
            errors: [],
            msg: undefined
        }
    },
    methods: {
        load: function () {
            this.loaded = false
            this.axios.get(this.url(`/api/settings/get_call_history`)).then((response) => {
                this.calls = response.data
                    .sort((a, b) => a.connected_timestamp - b.connected_timestamp)
                this.calls.forEach(call => {
                    call.start_time = moment.unix(call.connected_timestamp).format('DD.MM.YYYY в HH:mm')
                    if (call.duration) {
                        let hours = Math.floor(call.duration / (60 * 60))
                        let minutes = Math.floor((call.duration % (60 * 60)) / 60)
                        let seconds = (call.duration % (60 * 60)) % 60
                        call.duration_description = `${hours ? hours + ' ч. ' : ''}${minutes ? minutes + ' мин. ' : ''}${seconds} сек.`
                    } else {
                        call.duration_description = 'Звонок не состоялся'
                    }
                })
            })
            this.$forceUpdate()
            this.loaded = true
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
