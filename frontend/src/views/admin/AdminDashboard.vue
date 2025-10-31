<template>
  <div class="dashboard">
    <section class="card">
      <header>
        <h2>验证码类型管理</h2>
        <button type="button" @click="loadCaptchaTypes">刷新</button>
      </header>
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>描述</th>
            <th>默认</th>
            <th>启用</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in captchaTypes" :key="item.id">
            <td>{{ item.type_name }}</td>
            <td>{{ item.description }}</td>
            <td>
              <input type="radio" name="defaultType" :checked="item.is_default" @change="setDefault(item)" />
            </td>
            <td>
              <input type="checkbox" :checked="item.enabled" @change="toggleEnabled(item)" />
            </td>
            <td>
              <button type="button" @click="disableType(item)" class="danger">禁用</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="card">
      <header>
        <h2>登录记录</h2>
        <button type="button" @click="loadLoginRecords">刷新</button>
      </header>
      <table>
        <thead>
          <tr>
            <th>用户</th>
            <th>时间</th>
            <th>IP</th>
            <th>验证码</th>
            <th>结果</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in loginRecords" :key="record.id">
            <td>{{ record.username }}</td>
            <td>{{ record.login_time }}</td>
            <td>{{ record.ip_address }}</td>
            <td>{{ record.captcha_type }}</td>
            <td>
              <span :class="{ success: record.success, error: !record.success }">{{ record.success ? '成功' : '失败' }}</span>
            </td>
            <td>{{ record.message }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script>
import { del, get, post } from '@/services/api'

export default {
  name: 'AdminDashboard',
  data () {
    return {
      captchaTypes: [],
      loginRecords: []
    }
  },
  methods: {
    async loadCaptchaTypes () {
      const res = await get('/admin/captcha_types')
      if (res.data.success) this.captchaTypes = res.data.data.items
    },
    async loadLoginRecords () {
      const { data } = await get('/admin/login_records')
      if (data.success) {
        this.loginRecords = data.data.records
      }
    },
    async setDefault (item) {
      await post('/admin/captcha_types', {
        type_name: item.type_name,
        is_default: true,
        enabled: true,
        description: item.description,
        config: item.config
      })
      this.loadCaptchaTypes()
    },
    async toggleEnabled (item) {
      await post('/admin/captcha_types', {
        type_name: item.type_name,
        is_default: item.is_default,
        enabled: !item.enabled,
        description: item.description,
        config: item.config
      })
      this.loadCaptchaTypes()
    },
    async disableType (item) {
      await del('/admin/captcha_types', { type_name: item.type_name })
      this.loadCaptchaTypes()
    }
  },
  async mounted () {
    await Promise.all([this.loadCaptchaTypes(), this.loadLoginRecords()])
  }
}
</script>

<style scoped>
.dashboard {
  display: grid;
  gap: 2rem;
}

.card {
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

header h2 {
  margin: 0;
}

header button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

button.danger {
  padding: 0.3rem 0.6rem;
  background: #dc2626;
  color: #fff;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}

.success {
  color: #15803d;
}

.error {
  color: #dc2626;
}
</style>
