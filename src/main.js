import Vue from 'vue'
import App from './App'

import VueConfirmDialog from 'vue-confirm-dialog';
import DatePicker from 'vue2-datepicker';
import 'vue2-datepicker/index.css';
import 'vue2-datepicker/locale/ru';

import axios from "axios";

window.Event = new class {
    constructor() {
        this.vue = new Vue();
    }

    fire(event, data = null) {
        if (!data && data !== 0) {
            console.log('sending event', event);
        } else {
            console.log('sending event', event, 'with data', data);
        }

        this.vue.$emit(event, data);
    }

    listen(event, callback) {
        this.vue.$on(event, callback);
    }
};

Vue.mixin({
    methods: {
        url: function (action) {
            let api_host = window.API_HOST;
            let agent_token = window.AGENT_TOKEN;
            let contract_id = window.CONTRACT_ID;
            let agent_id = window.AGENT_ID;

            return api_host + '/api/client/agents/' + agent_id + '/?action=' + action + '&contract_id=' + contract_id + '&agent_token=' + agent_token
        },
        image_url: function (file_name) {
            return 'https://common.medsenger.ru/images/' + file_name
        },
        isJsonString: function (str) {
            if (!str)
                return true;
            try {
                JSON.parse(str);
            } catch (e) {
                return false;
            }
            return true;
        },
        to_float: function (val) {
            return parseFloat(val.toString().replace(',', '.'))
        },
        copy: function (to, from) {
            Object.keys(from).forEach(k => {
                to[k] = from[k]
            })
        },
    },
    computed: {
        mobile() {
            return window.innerWidth < window.innerHeight
        }
    },
    data() {
        return {
            current_contract_id: window.CONTRACT_ID,
            weekdays: ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
            short_weekdays: ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'],
            axios: require('axios'),
            images: {
                ok: this.image_url('icons8-ok-128.png'),
                error: this.image_url('icons8-delete-128.png'),
                video_call: this.image_url('icons8-videocall-100.png'),
                start_video_call: this.image_url('icons8-chatting-100.png'),
                nothing_found: this.image_url('icons8-nothing-found-100.png'),
                call: this.image_url('icons8-phone-96.png'),
                disconnected_call: this.image_url('icons8-call-disconnected-96.png')
            },
            window_mode: window.MODE,
            current_doctor_id: window.PARAMS.doctor_id
        }
    }
})

Vue.use(VueConfirmDialog)
Vue.component('vue-confirm-dialog', VueConfirmDialog.default)
Vue.component('date-picker', DatePicker)

new Vue({
    el: '#app',
    render: h => h(App),
})
