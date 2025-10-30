<template>
  <div class="success-page">
    <div class="card">
      <h2>登录成功</h2>
      <p>欢迎回来，{{ user?.username }}！</p>
      <p v-if="user?.is_staff">您拥有管理员权限。</p>
      <div class="actions">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SuccessView',
  data () {
    return {
      user: null
    }
  },
  created () {
    const stored = window.localStorage.getItem('currentUser')
    if (stored) {
      this.user = JSON.parse(stored)
    }
  }
}
</script>

<style scoped>
.success-page {
  display: flex;
  justify-content: center;
}

.card {
  width: 360px;
  padding: 2rem;
  border-radius: 16px;
  background: #ecfdf5;
  color: #064e3b;
  text-align: center;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.1);
}

a {
  color: #2563eb;
}
</style>
