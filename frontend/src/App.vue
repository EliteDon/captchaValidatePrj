<template>
  <div id="app">
    <header class="app-header">
      <h1>验证码验证系统</h1>
      <nav>
        <router-link to="/login">用户登录</router-link>
        <router-link to="/register">注册</router-link>
        <router-link to="/admin/login">管理员入口</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f3f6fb;
  color: #1f2933;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #1e3a8a;
  color: #fff;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

nav {
  display: flex;
  gap: 1rem;
}

a {
  color: #bfdbfe;
}

a.router-link-exact-active {
  color: #fff;
  font-weight: bold;
}

main {
  flex: 1;
  padding: 2rem;
}
</style>
