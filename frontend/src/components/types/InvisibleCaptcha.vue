<template>
  <div class="invisible-captcha">
    <p>请稍候片刻，我们正在校验您的操作行为。</p>
    <div class="timer">已停留：{{ elapsed.toFixed(1) }} 秒</div>
    <label class="honeypot">
      联系方式（请勿填写）：
      <input v-model="honeypot" type="text" placeholder="请留空" />
    </label>
  </div>
</template>

<script>
export default {
  name: 'InvisibleCaptcha',
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
  data () {
    return {
      start: Date.now(),
      elapsed: 0,
      honeypot: this.value.honeypot || ''
    }
  },
  mounted () {
    this.interval = setInterval(() => {
      this.elapsed = (Date.now() - this.start) / 1000
      this.emitValue()
    }, 200)
  },
  beforeDestroy () {
    clearInterval(this.interval)
  },
  watch: {
    value: {
      deep: true,
      handler (val) {
        if (val && typeof val.honeypot !== 'undefined') {
          this.honeypot = val.honeypot
        }
      }
    },
    honeypot () {
      this.emitValue()
    }
  },
  methods: {
    emitValue () {
      this.$emit('input', { duration: this.elapsed, honeypot: this.honeypot })
    }
  }
}
</script>

<style scoped>
.invisible-captcha {
  display: grid;
  gap: 0.75rem;
}

.timer {
  font-size: 1.1rem;
  font-weight: bold;
  color: #0f172a;
}

.honeypot input {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #cbd5f5;
}
</style>
