<template>
    <div>
        <h3 style="text-align: center; margin-bottom: 15px;">Ошибка загрузки</h3>

        <p style="text-align: center"><img :src="images.error" /></p>

        <p style="text-align: center">
            <small>Запрошенный контент недоступен.</small>
        </p>

        <p style="text-align: center">
            <button class="btn btn-danger" @click="close()">Закрыть окно</button>
        </p>
    </div>
</template>

<script>
export default {
    name: "LoadError",
    methods: {
        close: function () {
            window.parent.postMessage('close-modal', '*');
        }
    },
    mounted() {
    }
}
</script>

<style scoped>

</style>
