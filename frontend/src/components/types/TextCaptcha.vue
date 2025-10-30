<template>
  <div class="text-captcha">
    <div class="code-display">{{ challenge.payload.text }}</div>
    <input v-model="code" type="text" placeholder="输入验证码" />
  </div>
</template>

<script>
export default {
  name: 'TextCaptcha',
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
    code: {
      get () {
        return this.value.code || ''
      },
      set (val) {
        this.$emit('input', { ...this.value, code: val })
      }
    }
  }
}
</script>

<style scoped>
.text-captcha {
  display: grid;
  gap: 0.75rem;
}

.code-display {
  font-size: 1.6rem;
  letter-spacing: 0.4rem;
  padding: 0.75rem;
  text-align: center;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  font-weight: bold;
}

input {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}
</style>
