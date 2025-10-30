<template>
  <div class="grid-captcha">
    <div class="grid">
      <button
        v-for="(img, index) in challenge.payload.images"
        :key="index"
        type="button"
        :class="{ active: selected.includes(index) }"
        @click="toggle(index)"
      >
        {{ index + 1 }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GridCaptcha',
  props: {
    value: {
      type: Object,
      default: () => ({ indexes: [] })
    },
    challenge: {
      type: Object,
      required: true
    }
  },
  computed: {
    selected () {
      return this.value.indexes || []
    }
  },
  methods: {
    toggle (index) {
      const next = new Set(this.selected)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      this.$emit('input', { ...this.value, indexes: Array.from(next).sort((a, b) => a - b) })
    }
  }
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

button {
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  border: 1px solid #cbd5f5;
  background: #f1f5f9;
  color: #1e293b;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

button.active {
  background: #2563eb;
  color: #fff;
  border-color: #1e3a8a;
}
</style>
