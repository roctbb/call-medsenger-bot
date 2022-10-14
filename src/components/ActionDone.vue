<template>
    <div>
        <h3 style="text-align: center; margin-bottom: 15px;">Действие подтверждено</h3>

        <p style="text-align: center"><img :src="images.ok" /></p>

        <p style="text-align: center">
            <small>Окно закроется автоматически через секунду. Если не закрылось - нажмите кнопку.</small>
        </p>

        <p style="text-align: center">
            <button class="btn btn-success" @click="close()">Закрыть окно</button>
        </p>
    </div>
</template>

<script>
export default {
    name: "ActionDone",
    methods: {
        close: function () {
            window.parent.postMessage('close-modal-success', '*');
        }
    },
    mounted() {
        setTimeout(this.close, 1000);
    }
}
</script>

<style scoped>

</style>
