<template>
  <div v-if="visible" class="modal-backdrop">
    <div class="modal">
      <header>
        <h3>请完成验证码验证</h3>
        <button class="close" @click="$emit('close')">×</button>
      </header>
      <section v-if="challenge">
        <p class="hint">{{ challenge.payload.hint }}</p>
        <div class="captcha-body">
          <component :is="currentView" :challenge="challenge" v-model="formState" />
        </div>
      </section>
      <footer>
        <button class="secondary" @click="$emit('refresh')">换一张</button>
        <button class="primary" @click="handleConfirm">确认</button>
      </footer>
    </div>
  </div>
</template>

<script>
import TextCaptcha from './types/TextCaptcha.vue'
import ArithmeticCaptcha from './types/ArithmeticCaptcha.vue'
import SliderCaptcha from './types/SliderCaptcha.vue'
import GridCaptcha from './types/GridCaptcha.vue'
import BehaviorCaptcha from './types/BehaviorCaptcha.vue'
import CodeCaptcha from './types/CodeCaptcha.vue'
import InvisibleCaptcha from './types/InvisibleCaptcha.vue'

const typeViews = {
  text: TextCaptcha,
  arithmetic: ArithmeticCaptcha,
  slider: SliderCaptcha,
  grid: GridCaptcha,
  behavior: BehaviorCaptcha,
  email: CodeCaptcha,
  sms: CodeCaptcha,
  voice: CodeCaptcha,
  invisible: InvisibleCaptcha
}

export default {
  name: 'CaptchaModal',
  components: typeViews,
  props: {
    visible: Boolean,
    challenge: Object
  },
  data () {
    return {
      formState: {}
    }
  },
  computed: {
    currentView () {
      return typeViews[this.challenge?.type] || TextCaptcha
    }
  },
  watch: {
    challenge: {
      immediate: true,
      handler () {
        this.formState = {}
      }
    }
  },
  methods: {
    handleConfirm () {
      this.$emit('confirm', {
        type: this.challenge?.type,
        value: this.formState
      })
    }
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2);
  overflow: hidden;
  animation: fadeIn 0.2s ease;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #1e3a8a;
  color: #fff;
}

header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.close {
  border: none;
  background: transparent;
  color: #fff;
  font-size: 1.5rem;
  cursor: pointer;
}

section {
  padding: 1.5rem;
}

.hint {
  margin-bottom: 1rem;
  color: #334155;
}

footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: #f8fafc;
}

button {
  border-radius: 6px;
  padding: 0.5rem 1rem;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
}

button.primary {
  background: #2563eb;
  color: #fff;
}

button.secondary {
  background: #e2e8f0;
  color: #0f172a;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
