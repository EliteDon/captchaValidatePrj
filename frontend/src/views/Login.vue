<template>
  <div class="page">
    <div class="card">
      <h2>用户登录</h2>
      <form @submit.prevent="handleSubmit">
        <label>
          用户名
          <input v-model="form.username" type="text" required />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" required />
        </label>
        <div class="actions">
          <button type="button" class="secondary" @click="openCaptcha">获取验证码</button>
          <button type="submit" class="primary">登录</button>
        </div>
      </form>
      <p v-if="message" :class="{ error: !success, success }">{{ message }}</p>
    </div>
    <CaptchaModal
      :visible="captcha.visible"
      :challenge="captcha.challenge"
      @close="captcha.visible = false"
      @refresh="fetchCaptcha"
      @confirm="verifyCaptcha"
    />
  </div>
</template>

<script>
import CaptchaModal from '@/components/CaptchaModal.vue'
import { post } from '@/services/api'

export default {
  name: 'LoginView',
  components: { CaptchaModal },
  data () {
    return {
      form: {
        username: '',
        password: ''
      },
      captcha: {
        visible: false,
        challenge: null,
        answer: null,
        verified: false
      },
      message: '',
      success: false,
      loading: false
    }
  },
  methods: {
    async openCaptcha () {
      if (!this.captcha.challenge) {
        await this.fetchCaptcha()
      }
      this.captcha.visible = true
    },
    async fetchCaptcha () {
      try {
        const { data } = await post('/captcha/request', {})
        if (data.data) {
          this.captcha.challenge = data.data
          this.captcha.visible = true
          this.captcha.answer = null
          this.captcha.verified = false
        }
      } catch (error) {
        this.message = error.message
        this.success = false
      }
    },
    async verifyCaptcha ({ value }) {
      if (!this.captcha.challenge) return
      try {
        const payload = {
          token: this.captcha.challenge.token,
          answer: value
        }
        const { data } = await post('/captcha/verify', payload)
        if (data.success) {
          this.captcha.verified = true
          this.captcha.answer = value
          this.message = '验证码通过，请继续登录'
          this.success = true
          this.captcha.visible = false
        } else {
          this.captcha.verified = false
          this.success = false
          this.message = data.message
          await this.fetchCaptcha()
        }
      } catch (error) {
        this.captcha.verified = false
        this.success = false
        this.message = error.message
        await this.fetchCaptcha()
      }
    },
    async handleSubmit () {
      if (this.loading) return
      if (!this.captcha.challenge || !this.captcha.verified) {
        this.message = '请先完成验证码验证'
        this.success = false
        await this.fetchCaptcha()
        return
      }
      try {
        this.loading = true
        const payload = {
          username: this.form.username,
          password: this.form.password,
          captcha_token: this.captcha.challenge.token
        }
        const { data } = await post('/login', payload)
        this.loading = false
        if (data.success) {
          this.success = true
          this.message = data.message
          window.localStorage.setItem('currentUser', JSON.stringify(data.data))
          this.$router.push('/success')
        } else {
          this.success = false
          this.message = data.message
          await this.fetchCaptcha()
        }
      } catch (error) {
        this.loading = false
        this.success = false
        this.message = error.message
        await this.fetchCaptcha()
      }
    }
  },
  async mounted () {
    await this.fetchCaptcha()
  }
}
</script>

<style scoped>
.page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.card {
  width: 360px;
  padding: 2rem;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.1);
  display: grid;
  gap: 1rem;
}

h2 {
  margin: 0;
  text-align: center;
}

label {
  display: grid;
  gap: 0.4rem;
  font-size: 0.95rem;
}

input {
  padding: 0.75rem;
  border-radius: 10px;
  border: 1px solid #cbd5f5;
}

.actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

button {
  flex: 1;
  padding: 0.7rem 1rem;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 1rem;
}

button.primary {
  background: #2563eb;
  color: #fff;
}

button.secondary {
  background: #e2e8f0;
  color: #1e293b;
}

p.error {
  color: #dc2626;
}

p.success {
  color: #15803d;
}
</style>
