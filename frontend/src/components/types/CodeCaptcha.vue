<template>
  <div class="code-captcha">
    <div class="target">{{ targetText }}</div>
    <input v-model="code" type="text" maxlength="6" placeholder="输入6位验证码" />
  </div>
</template>

<script>
export default {
  name: 'CodeCaptcha',
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
    },
    targetText () {
      const { type, payload } = this.challenge
      if (type === 'email') {
        return `验证码发送至：${payload.maskedEmail}`
      }
      if (type === 'sms') {
        return `验证码发送至：${payload.maskedPhone}`
      }
      if (type === 'voice') {
        return '请聆听语音播报并输入数字'
      }
      return ''
    }
  }
}
</script>

<style scoped>
.code-captcha {
  display: grid;
  gap: 0.75rem;
}

.target {
  font-size: 1rem;
  color: #1e293b;
}

input {
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}
</style>
