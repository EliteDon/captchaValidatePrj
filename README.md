# 验证码验证系统（Captcha Validate System）

本项目实现了一个前后端分离的验证码验证平台，包含用户侧注册 / 登录流程以及后台验证码配置和登录记录查看功能。

## 项目结构

```
.
├── backend/              # Django 5 后端代码
│   ├── manage.py
│   ├── captcha_backend/  # 项目配置
│   ├── accounts/         # 用户、登录相关接口
│   └── captcha/          # 验证码类型与验证逻辑
├── frontend/             # Vue 2 + Vite 前端代码
│   ├── index.html
│   ├── src/
│   └── package.json
└── README.md
```

## 后端（Django）

### 运行环境

- Python 3.10+
- SQL Server（默认连接到 `captcha_validate_system`，用户名 `sa`，密码 `root`）

安装依赖：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows 使用 venv\Scripts\activate
pip install -r requirements.txt
```

执行迁移并启动服务：

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

后端提供以下主要接口：

- `POST /api/register` 用户注册
- `POST /api/login` 用户登录（需要先完成验证码）
- `POST /api/captcha/request` 申请验证码
- `POST /api/captcha/verify` 校验验证码
- `POST /api/admin/login` 管理员登录
- `GET/POST/DELETE /api/admin/captcha_types` 管理验证码类型
- `GET /api/admin/login_records` 查看登录记录

默认会创建两个账号：

- 普通用户：`test_user` / `TestUser123!`
- 管理员：`admin` / `Admin123!`

## 前端（Vue 2）

### 运行环境

- Node.js 18+

安装依赖并启动开发服务器：

```bash
cd frontend
npm install
npm run dev
```

前端使用 Vue Router 管理页面：

- `/login` 用户登录（弹窗验证码）
- `/register` 用户注册
- `/success` 登录成功页
- `/admin/login` 管理员登录
- `/admin/dashboard` 后台管理

验证码弹窗支持九种验证码类型：文本、算术、滑块、九宫格、行为轨迹、邮箱、短信、语音与无感验证。

## 其他说明

- 所有接口返回统一结构：`{ success, message, data }`
- 前端通过 Axios 对 `/api/*` 发起请求，开发环境自动代理到本地 Django 服务。
- 管理后台展示验证码类型配置，并提供登录记录分页基础结构（默认取最近 200 条）。
- 后端已在 Python 3.10 环境下验证通过，如需在其他版本运行请确保 `pyodbc` 具备对应的编译环境。

欢迎根据实际业务需求继续扩展。
