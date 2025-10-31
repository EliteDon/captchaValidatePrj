import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import CaptchaGenerationError, CaptchaService


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


logger = logging.getLogger(__name__)


@csrf_exempt
def request_captcha(request):
    if request.method != 'POST':
        return build_response(False, '仅支持POST请求')
    data = parse_body(request)
    requested_type = data.get('type')
    client_ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    service = CaptchaService()
    try:
        challenge = service.generate_challenge(
            client_ip=client_ip,
            user_agent=user_agent,
            requested_type=requested_type,
            request_data=data,
        )
    except CaptchaGenerationError as exc:
        return build_response(False, str(exc))
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception('生成验证码失败: %s', exc)
        return build_response(False, '验证码生成失败，请稍后再试')

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
