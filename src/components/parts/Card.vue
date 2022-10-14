<template>
    <div>
        <div class="card"  :class="additional_class" :style="bg">
            <div class="card-body">
                <h5 class="card-title" v-if="title">{{ title }}</h5>
                <slot></slot>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: "Card",
    props: ['title', 'image', 'additional_class'],
    computed: {
        bg: function () {
            if (this.image)
            {
                return "background-image: url('" + this.image + "'); "
            }
            else {
                return "background-image: none;"
            }
        }
    }
}
</script>

<style scoped>
.card {
    margin-bottom: 15px;
    background-repeat: no-repeat;
    background-position: right bottom;
    background-size: 55px;
}

.card a {
    font-size: 0.75rem;

}
</style>
