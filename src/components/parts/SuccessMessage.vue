<template>
    <div class="alert alert-success" role="alert" v-if="message">
        <span v-html="message"/>
    </div>

</template>

<script>
import * as moment from "moment/moment";

export default {
    name: "SuccessMessage",
    props: ['message'],
    data() {
        return {
            time: ''
        }
    },
    mounted() {
        this.time = moment().format('HH:mm')
    }
}
</script>

<style scoped>
    ul {
        margin: 0;
    }
    .alert {
        margin-top: 15px;
    }
</style>
