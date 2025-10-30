import Vue from 'vue'
import Router from 'vue-router'

import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Success from '@/views/Success.vue'
import AdminLogin from '@/views/admin/AdminLogin.vue'
import AdminDashboard from '@/views/admin/AdminDashboard.vue'

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/success', component: Success },
    { path: '/admin/login', component: AdminLogin },
    { path: '/admin/dashboard', component: AdminDashboard }
  ]
})

export default router
