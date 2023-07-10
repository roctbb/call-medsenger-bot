<template>
    <div>
        <div class="btn-group">
            <button :class="'btn btn-sm ' + btn_color('timetable')"
                    @click="change_state('timetable')">Расписание
            </button>
            <button :class="'btn btn-sm ' + btn_color('calls')"
                    @click="change_state('calls')">Ближайшие звонки
            </button>
        </div>

        <div style="margin-top: 10px" v-if="state == 'timetable'">
            <timetable :patient="patient"/>
        </div>
        <div style="margin-top: 10px" v-if="state == 'calls'">
            <calls-list source="doctor"/>
        </div>
    </div>
</template>

<script>

import Timetable from "../views/Timetable";
import axios from "axios";
import Call from "../views/Call";
import CallsList from "../views/CallsList";

export default {
    name: "Dashboard",
    components: {CallsList, Call, Timetable},
    props: {
        patient: {
            required: true
        }
    },
    data: function () {
        return {
            state: 'timetable',
            loaded: false,
            errors: []
        }
    },
    methods: {
        btn_color: function (btn) {
            return this.state == btn ? 'btn-primary' : 'btn-secondary'
        },
        change_state: function (state) {
            this.state = state
        },
    },
    computed: {},
    mounted() {
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
p {
    margin-top: 5px;
    margin-bottom: 5px;
}

h5 {
    margin-bottom: 10px;
    margin-top: 10px;
    font-size: 1.15rem;
}

small {
    font-size: 90%;
}

.card a {
    font-size: 90% !important;
}

</style>
