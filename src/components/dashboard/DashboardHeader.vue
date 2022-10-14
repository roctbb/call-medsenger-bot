<template>
    <div style="background-color: white;">
        <div class="container" v-if="patient">
            <div class="row">
                <div class="col-12">
                    <p><strong>Пациент:</strong> {{ patient.name }} ({{ patient.birthday }}) <span class="float-right"></span></p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: "DashboardHeader",
    props: ['patient'],
    methods: {
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
}
</style>
