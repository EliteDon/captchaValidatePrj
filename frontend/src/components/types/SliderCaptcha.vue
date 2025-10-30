<template>
  <div class="slider-captcha">
    <div class="slider-view">
      <div class="background">{{ challenge.payload.image }}</div>
      <div class="piece" :style="{ left: sliderValue + '%' }">拼图</div>
    </div>
    <input v-model.number="sliderValue" type="range" min="0" max="100" />
  </div>
</template>

<script>
export default {
  name: 'SliderCaptcha',
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
    sliderValue: {
      get () {
        return this.value.offset ?? 50
      },
      set (val) {
        this.$emit('input', { ...this.value, offset: Number(val) })
      }
    }
  }
}
</script>

<style scoped>
.slider-captcha {
  display: grid;
  gap: 0.75rem;
}

.slider-view {
  position: relative;
  background: linear-gradient(135deg, #c7d2fe, #e0e7ff);
  border-radius: 12px;
  padding: 1rem;
  color: #1e3a8a;
  text-align: center;
}

.piece {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  padding: 0.35rem 0.75rem;
  background: #2563eb;
  color: #fff;
  border-radius: 999px;
  transition: left 0.2s ease;
}
</style>
