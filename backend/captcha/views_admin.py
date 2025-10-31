import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import CaptchaType


def _resp(success: bool, message: str = '', data=None) -> JsonResponse:
    return JsonResponse({'success': success, 'message': message, 'data': data or {}})


def _parse(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@method_decorator([csrf_exempt, login_required, user_passes_test(lambda u: u.is_staff)], name='dispatch')
class AdminCaptchaTypeView(View):
    def get(self, request):
        items = [
            {
                'id': captcha_type.id,
                'type_name': captcha_type.type_name,
                'description': captcha_type.description,
                'enabled': captcha_type.enabled,
                'is_default': captcha_type.is_default,
                'config': json.loads(captcha_type.config_json or '{}'),
                'updated_at': captcha_type.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for captcha_type in CaptchaType.objects.all().order_by('type_name')
        ]
        default_type = CaptchaType.objects.filter(is_default=True).values_list('type_name', flat=True).first()
        return _resp(True, 'ok', {'items': items, 'default_type': default_type})

    def post(self, request):
        data = _parse(request)
        type_name = data.get('type_name')
        if not type_name:
            return _resp(False, '缺少 type_name')

        captcha_type, _ = CaptchaType.objects.update_or_create(
            type_name=type_name,
            defaults={
                'description': data.get('description', ''),
                'enabled': data.get('enabled', True),
                'config_json': json.dumps(data.get('config', {}), ensure_ascii=False),
                'is_default': data.get('is_default', False),
            },
        )

        if captcha_type.is_default:
            CaptchaType.objects.exclude(id=captcha_type.id).update(is_default=False)

        return _resp(True, '保存成功', {'type_name': type_name})

    def delete(self, request):
        data = _parse(request)
        type_name = data.get('type_name')
        if not type_name:
            return _resp(False, '缺少 type_name')

        updated = CaptchaType.objects.filter(type_name=type_name).update(enabled=False, is_default=False)
        if not updated:
            return _resp(False, '验证码类型不存在')
        return _resp(True, f'{type_name} 已禁用')
