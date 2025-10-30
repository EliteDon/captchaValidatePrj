import json
from datetime import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import update_last_login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from captcha.services import CaptchaService

from .models import LoginRecord, User


def build_response(success: bool, message: str, data=None) -> JsonResponse:
    payload = {
        'success': success,
        'message': message,
        'data': data or {},
    }
    return JsonResponse(payload)


def parse_body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def get_client_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')

    data = parse_body(request)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password or not email:
        return build_response(False, '用户名、密码、邮箱均不能为空')

    if User.objects.filter(username=username).exists():
        return build_response(False, '用户名已存在')

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_active=True,
    )

    return build_response(True, '注册成功', {'id': user.id, 'username': user.username})


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')

    data = parse_body(request)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    captcha_token = data.get('captcha_token')
    captcha_value = data.get('captcha_value')

    if not username or not password:
        return build_response(False, '用户名和密码不能为空')

    if not captcha_token:
        return build_response(False, '请先通过验证码验证')

    client_ip = get_client_ip(request)

    captcha_service = CaptchaService()
    if captcha_value is not None:
        captcha_ok, captcha_message, captcha_type = captcha_service.validate_and_consume(
            token=captcha_token,
            user_answer=captcha_value,
            client_ip=client_ip,
        )
    else:
        captcha_ok, captcha_message, captcha_type = captcha_service.consume_verified_token(
            token=captcha_token,
            client_ip=client_ip,
        )

    existing_user = User.objects.filter(username=username).first()

    if not captcha_ok:
        if existing_user:
            LoginRecord.objects.create(
                user=existing_user,
                ip_address=client_ip,
                success=False,
                captcha_type=captcha_type or 'unknown',
                message=f'验证码失败: {captcha_message}',
            )
        return build_response(False, captcha_message or '验证码验证失败')

    user = authenticate(request, username=username, password=password)
    if user is None:
        if existing_user:
            LoginRecord.objects.create(
                user=existing_user,
                ip_address=client_ip,
                success=False,
                captcha_type=captcha_type or 'unknown',
                message='用户名或密码错误',
            )
        return build_response(False, '用户名或密码错误')

    login(request, user)
    user.ip_address = client_ip
    user.last_login = datetime.now()
    user.save(update_fields=['ip_address', 'last_login'])
    update_last_login(None, user)

    LoginRecord.objects.create(
        user=user,
        ip_address=client_ip,
        success=True,
        captcha_type=captcha_type or 'unknown',
        message='登录成功',
    )

    return build_response(True, '登录成功', {'username': user.username, 'is_staff': user.is_staff})


@csrf_exempt
def admin_login(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')

    data = parse_body(request)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return build_response(False, '用户名和密码不能为空')

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_staff:
        return build_response(False, '管理员账号或密码错误')

    login(request, user)
    user.ip_address = get_client_ip(request)
    user.last_login = datetime.now()
    user.save(update_fields=['ip_address', 'last_login'])

    return build_response(True, '管理员登录成功', {'username': user.username})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_login_records(request):
    records = LoginRecord.objects.select_related('user').all()[:200]
    data = [
        {
            'id': record.id,
            'username': record.user.username,
            'login_time': record.login_time.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': record.ip_address,
            'success': record.success,
            'captcha_type': record.captcha_type,
            'message': record.message,
        }
        for record in records
    ]
    return build_response(True, '获取成功', {'records': data})
