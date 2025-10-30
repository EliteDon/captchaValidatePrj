<template>
  <div class="arithmetic-captcha">
    <div class="expression">{{ challenge.payload.expression }} = ?</div>
    <input v-model="result" type="number" placeholder="输入结果" />
  </div>
</template>

<script>
export default {
  name: 'ArithmeticCaptcha',
  props: {
    value: {
      type: Object,
      default: () => ({})
    },
    challenge: {
      type: Object,
      required: true
    }
  },
  computed: {
    result: {
      get () {
        return this.value.result || ''
      },
      set (val) {
        this.$emit('input', { ...this.value, result: val })
      }
    }
  }
}
</script>

<style scoped>
.arithmetic-captcha {
  display: grid;
  gap: 0.75rem;
}

.expression {
  font-size: 1.4rem;
  text-align: center;
  font-weight: bold;
}

input {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}
</style>
