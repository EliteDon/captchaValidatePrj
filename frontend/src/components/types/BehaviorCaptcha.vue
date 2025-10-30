<template>
  <div class="behavior-captcha">
    <p>请模拟拖动，点击按钮达到 {{ challenge.payload.requiredSteps }} 次</p>
    <div class="counter">当前步数：{{ steps }}</div>
    <button type="button" @click="increment">拖动一次</button>
  </div>
</template>

<script>
export default {
  name: 'BehaviorCaptcha',
  props: {
    value: {
      type: Object,
      default: () => ({ steps: 0, completed: false })
    },
    challenge: {
      type: Object,
      required: true
    }
  },
  computed: {
    steps () {
      return this.value.steps || 0
    }
  },
  methods: {
    increment () {
      const nextSteps = this.steps + 1
      const completed = nextSteps >= this.challenge.payload.requiredSteps
      this.$emit('input', { steps: nextSteps, completed })
    }
  }
}
</script>

<style scoped>
.behavior-captcha {
  display: grid;
  gap: 0.75rem;
  text-align: center;
}

.counter {
  font-size: 1.1rem;
  font-weight: bold;
}

button {
  padding: 0.6rem 1rem;
  border-radius: 6px;
  border: none;
  background: #34d399;
  color: #064e3b;
  cursor: pointer;
}
</style>
