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

### 环境变量配置

后端启动前需要在 `backend/.env` 中填入数据库、邮件与 Twilio 信息。可参考根目录下的 `.env` 模板：

```env
# --- 数据库配置 ---
DB_ENGINE=mssql
DB_NAME=captcha_validate_system
DB_USER=sa
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=1433

# --- 邮件配置 ---
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_email_smtp_key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=验证码系统 <your_email@qq.com>

# --- Twilio 配置 ---
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+10000000000
TEST_PHONE_NUMBER=+8613800000000

# --- 站点配置 ---
SITE_URL=http://127.0.0.1:8000
DEBUG=True
```

若暂时没有真实邮箱或 Twilio 账号，可以为 `EMAIL_HOST_USER` / `TWILIO_*` 设置假值，并在 `captcha_type` 表的 `config_json` 中预填 `target_email` 或 `target_phone` 来使用测试账号发送验证码。

### 核心接口说明

后端提供以下主要接口：

- `POST /api/register` 用户注册
- `POST /api/login` 用户登录（需要先完成验证码）
- `POST /api/captcha/request` 申请验证码
- `POST /api/captcha/verify` 校验验证码
- `POST /api/admin/login` 管理员登录
- `GET/POST/DELETE /api/admin/captcha_types` 管理验证码类型
- `GET /api/admin/login_records` 查看登录记录

调用流程示例：

1. 前端在用户点击注册 / 登录时先调用 `POST /api/captcha/request`，传入需要的验证码类型（`type` 字段）及目标邮箱 / 手机号；
2. 接收返回的 `token` 与验证码显示数据，展示给用户；
3. 用户输入验证码后，前端将 `token` 与答案 `answer` 一并传给 `POST /api/captcha/verify`；
4. 验证成功后即可继续注册或登录接口。

九类验证码均在同一接口中实现：

| 类型 | 请求数据要求 | 说明 |
| --- | --- | --- |
| `text` | 无 | 返回图形验证码文本 | 
| `arithmetic` | 无 | 返回算术表达式 | 
| `slider` | 无 | 返回滑块背景与缺口图片 | 
| `grid` | 无 | 返回九宫格图片及目标提示 | 
| `behavior` | 无 | 返回需要完成的轨迹步骤数 | 
| `email` | `email` 或 `target_email` | 发送 6 位数字验证码邮件 | 
| `sms` | `phone` / `mobile` / `target_phone` | 通过 Twilio 发送短信验证码 | 
| `voice` | `phone` / `mobile` / `target_phone` | 通过 Twilio 语音播报验证码 | 
| `invisible` | 可选 `honeypot` 字段 | 返回无感验证策略（蜜罐 + 最小停留时间） |

所有类型都会将 `ttl` 写入数据库的 `config_json` 中，可在后台修改生效时间、模版文案等参数。

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

### 后台管理使用指南

1. 管理员登录后台后进入「验证码类型」页面；
2. 点击「设为默认」会立即更新数据库中其他类型的 `is_default=False`，刷新后仍保持；
3. 点击开关可启用 / 禁用对应类型（禁用后前台不会再返回该类型）；
4. 删除按钮会将 `enabled=False` 且 `is_default=False`，如需恢复可重新启用；
5. 修改完配置后点击保存即可实时影响用户侧验证码行为。

后台的所有操作都通过 `/api/admin/captcha_types` 接口持久化到 `CaptchaType` 表，并即时反馈到页面。

## 其他说明

- 所有接口返回统一结构：`{ success, message, data }`
- 前端通过 Axios 对 `/api/*` 发起请求，开发环境自动代理到本地 Django 服务。
- 管理后台展示验证码类型配置，并提供登录记录分页基础结构（默认取最近 200 条）。
- 后端已在 Python 3.10 环境下验证通过，如需在其他版本运行请确保 `pyodbc` 具备对应的编译环境。

欢迎根据实际业务需求继续扩展。
