<template>
  <div class="page">
    <div class="card">
      <h2>管理员登录</h2>
      <form @submit.prevent="handleSubmit">
        <label>
          用户名
          <input v-model="form.username" type="text" required />
        </label>
        <label>
          密码
          <input v-model="form.password" type="password" required />
        </label>
        <button type="submit" class="primary">登录后台</button>
      </form>
      <p v-if="message" :class="{ error: !success, success }">{{ message }}</p>
    </div>
  </div>
</template>

<script>
import { post } from '@/services/api'

export default {
  name: 'AdminLoginView',
  data () {
    return {
      form: {
        username: '',
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
        const { data } = await post('/admin/login', this.form)
        this.loading = false
        this.success = data.success
        this.message = data.message
        if (data.success) {
          window.sessionStorage.setItem('adminUser', JSON.stringify(data.data))
          this.$router.push('/admin/dashboard')
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
  border-radius: 16px;
  background: #fff7ed;
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
  border: 1px solid #fed7aa;
}

button {
  padding: 0.8rem;
  border-radius: 10px;
  border: none;
  background: #f97316;
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
