import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import CaptchaType
from .services import CaptchaService


def build_response(success: bool, message: str, data=None) -> JsonResponse:
    return JsonResponse({'success': success, 'message': message, 'data': data or {}})


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
def request_captcha(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')
    data = parse_body(request)
    requested_type = data.get('type')
    client_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    service = CaptchaService()
    challenge = service.generate_challenge(client_ip=client_ip, user_agent=user_agent, requested_type=requested_type)
    payload = {
        'token': challenge.token,
        'type': challenge.type,
        'payload': json.loads(challenge.payload),
        'expires_at': challenge.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
    }
    return build_response(True, '验证码生成成功', payload)


@csrf_exempt
def verify_captcha(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')

    data = parse_body(request)
    token = data.get('token')
    user_answer = data.get('answer')
    client_ip = get_client_ip(request)

    if not token:
        return build_response(False, '缺少验证码token')

    service = CaptchaService()
    ok, message, captcha_type = service.validate_and_consume(token=token, user_answer=user_answer, client_ip=client_ip)
    return build_response(ok, message, {'type': captcha_type})


@method_decorator([login_required, user_passes_test(lambda u: u.is_staff)], name='dispatch')
class AdminCaptchaTypeView:
    def __call__(self, request):
        if request.method == 'GET':
            return self._list()
        if request.method == 'POST':
            return self._upsert(request)
        if request.method == 'DELETE':
            return self._disable(request)
        return build_response(False, '不支持的请求方法')

    def _list(self):
        service = CaptchaService()
        default_type = service.get_default_type()
        types = CaptchaType.objects.all()
        data = [
            {
                'id': item.id,
                'type_name': item.type_name,
                'description': item.description,
                'enabled': item.enabled,
                'is_default': item.is_default,
                'config': json.loads(item.config_json or '{}') if item.config_json else {},
                'updated_at': item.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for item in types
        ]
        return build_response(True, '获取成功', {'items': data, 'default_type': default_type})

    def _upsert(self, request):
        data = parse_body(request)
        type_name = data.get('type_name')
        if not type_name:
            return build_response(False, '缺少type_name字段')

        config = data.get('config', {})
        is_default = bool(data.get('is_default'))
        enabled = data.get('enabled', True)
        description = data.get('description', '')

        captcha_type, _ = CaptchaType.objects.update_or_create(
            type_name=type_name,
            defaults={
                'description': description,
                'enabled': enabled,
                'config_json': json.dumps(config, ensure_ascii=False),
                'is_default': is_default,
            },
        )
        if is_default:
            CaptchaType.objects.exclude(id=captcha_type.id).update(is_default=False)

        return build_response(True, '保存成功', {
            'id': captcha_type.id,
            'type_name': captcha_type.type_name,
            'enabled': captcha_type.enabled,
            'is_default': captcha_type.is_default,
        })

    def _disable(self, request):
        data = parse_body(request)
        type_name = data.get('type_name')
        if not type_name:
            return build_response(False, '缺少type_name字段')
        updated = CaptchaType.objects.filter(type_name=type_name).update(enabled=False)
        if not updated:
            return build_response(False, '验证码类型不存在')
        return build_response(True, '已禁用', {'type_name': type_name})


admin_captcha_types = AdminCaptchaTypeView()
