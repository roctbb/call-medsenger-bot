<template>
    <div class="text-center">
        <p><img :src="images.start_video_call" height="110"></p>
        <div v-if="mode == 'main'">
            <button class="btn btn-lg btn-success" @click="start()">Начать конференцию</button>
        </div>
        <div v-else>
            <h3>Конференция запущена!</h3>
            <a class="btn btn-lg btn-primary" :href="call_url" target="_blank" @click="close()">Перейти к звонку в
                браузере</a>
            <a class="btn btn-lg btn-success" :href="join_url" target="_blank" @click="close()">Открыть в приложении
                Zoom</a>
        </div>
    </div>
</template>

<script>

export default {
    name: "Call",
    components: {},
    data: function () {
        return {
            mode: 'main',
            call_url: undefined,
            join_url: undefined
        }
    },
    methods: {
        start: function () {
            this.$confirm(
                {
                    message: `Начать конференцию сейчас?`,
                    button: {
                        no: 'Нет',
                        yes: 'Да'
                    },
                    callback: confirm => {
                        if (confirm) {
                            this.axios.get(this.url('get_call_url')).then(this.process_load_answer)
                        }
                    }
                }
            )
        },
        process_load_answer: function (response) {
            this.call_url = response.data.call_url
            this.join_url = response.data.join_url
            this.mode = 'started'
        },
        close: function () {
            Event.fire('action-done')
        }
    },
    created() {
    }
}
</script>

<style scoped>

</style>
