<template>
  <div class="page">
    <div class="card">
      <h2>用户注册</h2>
      <form @submit.prevent="handleSubmit">
        <label>
          用户名
          <input v-model="form.username" type="text" required />
        </label>
        <label>
          邮箱
          <input v-model="form.email" type="email" required />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" required />
        </label>
        <button type="submit" class="primary">注册</button>
      </form>
      <p v-if="message" :class="{ error: !success, success }">{{ message }}</p>
      <router-link to="/login">已有账号？前往登录</router-link>
    </div>
  </div>
</template>

<script>
import { post } from '@/services/api'

export default {
  name: 'RegisterView',
  data () {
    return {
      form: {
        username: '',
        email: '',
        password: ''
      },
      message: '',
      success: false,
      loading: false
    }
  },
  methods: {
    async handleSubmit () {
      if (this.loading) return
      try {
        this.loading = true
        const { data } = await post('/register', this.form)
        this.loading = false
        this.message = data.message
        this.success = data.success
        if (data.success) {
          this.$router.push('/login')
        }
      } catch (error) {
        this.loading = false
        this.success = false
        this.message = error.message
      }
    }
  }
}
</script>

<style scoped>
.page {
  display: flex;
  justify-content: center;
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

label {
  display: grid;
  gap: 0.4rem;
}

input {
  padding: 0.75rem;
  border-radius: 10px;
  border: 1px solid #cbd5f5;
}

button {
  padding: 0.8rem;
  border-radius: 10px;
  border: none;
  background: #0ea5e9;
  color: #fff;
  cursor: pointer;
}

p.error {
  color: #dc2626;
}

p.success {
  color: #15803d;
}
</style>
