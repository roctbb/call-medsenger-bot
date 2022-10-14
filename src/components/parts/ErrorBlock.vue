<template>
    <div class="alert alert-warning" role="alert" v-if="errors.length">
        <ul>
            <li v-for="error in errors"><span v-html="error"/></li>
        </ul>
    </div>

</template>

<script>
export default {
    name: "ErrorBlock",
    props: ['errors']
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
