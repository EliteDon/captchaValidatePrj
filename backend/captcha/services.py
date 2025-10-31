import json
import logging
import random
import string
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

try:
    from twilio.base.exceptions import TwilioException
    from twilio.rest import Client
except ImportError:  # pragma: no cover - optional dependency guard
    TwilioException = Exception  # type: ignore[assignment]
    Client = None  # type: ignore[assignment]

from .models import CaptchaChallenge, CaptchaType

logger = logging.getLogger(__name__)


class CaptchaGenerationError(Exception):
    """Raised when a captcha challenge cannot be created."""


@dataclass
class CaptchaGenerator:
    description: str
    generator: Callable[[dict], Tuple[dict, dict, int]]
    default_ttl: int = 180


def mask_email(value: str) -> str:
    if not value or '@' not in value:
        return value
    local, domain = value.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*' if local else '*' * 3
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f'{masked_local}@{domain}'


def mask_phone(value: str) -> str:
    if not value:
        return value
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) < 7:
        return value
    masked = f"{digits[:3]}****{digits[-4:]}"
    if value.strip().startswith('+') and not masked.startswith('+'):
        return f'+{masked}'
    return masked


class CaptchaService:
    def __init__(self) -> None:
        self._registry: Dict[str, CaptchaGenerator] = {}
        self._register_default_generators()
        self.ensure_types_exist()

    # region public api
    def get_default_type(self) -> str:
        default_type = CaptchaType.objects.filter(enabled=True, is_default=True).first()
        if default_type:
            return default_type.type_name
        fallback = CaptchaType.objects.filter(enabled=True).first()
        if fallback:
            return fallback.type_name
        return 'text'

    def generate_challenge(
        self,
        *,
        client_ip: str,
        user_agent: str = '',
        requested_type: str | None = None,
        request_data: dict | None = None,
    ) -> CaptchaChallenge:
        request_data = request_data or {}
        type_name = requested_type or self.get_default_type()
        captcha_type = self._get_enabled_type(type_name)
        if captcha_type is None:
            type_name = self.get_default_type()
            captcha_type = self._get_enabled_type(type_name)
        if captcha_type is None:
            raise CaptchaGenerationError('没有可用的验证码类型，请联系管理员')

        generator = self._registry[type_name]
        config = self._load_config(captcha_type)
        context = {'request': request_data, 'config': config, 'captcha_type': captcha_type}

        payload, answer, ttl = generator.generator(context)
        ttl = self._resolve_ttl(config, ttl or generator.default_ttl)

        challenge = CaptchaChallenge.create(
            type_name,
            json.dumps(payload, ensure_ascii=False),
            json.dumps(answer, ensure_ascii=False),
            client_ip=client_ip,
            user_agent=user_agent,
            ttl_seconds=ttl,
        )
        return challenge

    def validate_and_consume(self, *, token: str, user_answer: Any, client_ip: str) -> tuple[bool, str, str | None]:
        try:
            challenge = CaptchaChallenge.objects.get(token=token)
        except CaptchaChallenge.DoesNotExist:
            return False, '验证码不存在或已过期', None

        if challenge.client_ip != client_ip:
            return False, '请求IP与验证码不匹配', challenge.type
        if challenge.is_expired():
            return False, '验证码已过期', challenge.type
        if challenge.validated:
            return False, '验证码已验证，请重新获取', challenge.type

        expected = json.loads(challenge.answer)
        normalized_answer = self._normalize_answer(user_answer)

        verifier = getattr(self, f'_verify_{challenge.type}', None)
        if verifier is None:
            verifier = self._default_verify

        if verifier(expected, normalized_answer):
            challenge.validated = True
            challenge.save(update_fields=['validated'])
            return True, '验证码验证成功', challenge.type
        return False, '验证码答案错误', challenge.type

    def consume_verified_token(self, token: str, client_ip: str) -> tuple[bool, str, str | None]:
        try:
            challenge = CaptchaChallenge.objects.get(token=token)
        except CaptchaChallenge.DoesNotExist:
            return False, '验证码不存在或已过期', None

        if challenge.client_ip != client_ip:
            return False, '请求IP与验证码不匹配', challenge.type
        if challenge.is_expired():
            return False, '验证码已过期', challenge.type
        if not challenge.validated:
            return False, '请先完成验证码验证', challenge.type

        captcha_type = challenge.type
        challenge.delete()
        return True, '验证码校验通过', captcha_type

    def ensure_types_exist(self) -> None:
        with transaction.atomic():
            for type_name, generator in self._registry.items():
                defaults = {
                    'description': generator.description,
                    'enabled': True,
                    'config_json': json.dumps({'ttl': generator.default_ttl}, ensure_ascii=False),
                    'is_default': type_name == 'text',
                }
                captcha_type, created = CaptchaType.objects.get_or_create(type_name=type_name, defaults=defaults)
                if created:
                    continue

                updates = {}
                if not captcha_type.description:
                    updates['description'] = generator.description

                config = self._load_config(captcha_type)
                if 'ttl' not in config:
                    config['ttl'] = generator.default_ttl
                    updates['config_json'] = json.dumps(config, ensure_ascii=False)

                if updates:
                    for field, value in updates.items():
                        setattr(captcha_type, field, value)
                    captcha_type.save(update_fields=list(updates.keys()))
    # endregion

    # region generator registration
    def _register_default_generators(self) -> None:
        self._registry['text'] = CaptchaGenerator('字母数字组合验证码', self._generate_text, 180)
        self._registry['arithmetic'] = CaptchaGenerator('基础算术验证码', self._generate_arithmetic, 180)
        self._registry['slider'] = CaptchaGenerator('滑块拼图验证码', self._generate_slider, 240)
        self._registry['grid'] = CaptchaGenerator('九宫格图片选取验证码', self._generate_grid, 240)
        self._registry['behavior'] = CaptchaGenerator('行为轨迹验证码', self._generate_behavior, 240)
        self._registry['email'] = CaptchaGenerator('邮箱验证码', self._generate_email, 300)
        self._registry['sms'] = CaptchaGenerator('短信验证码', self._generate_sms, 300)
        self._registry['voice'] = CaptchaGenerator('语音验证码', self._generate_voice, 300)
        self._registry['invisible'] = CaptchaGenerator('无感知验证码', self._generate_invisible, 120)
    # endregion

    # region generators
    def _generate_text(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        payload = {
            'type': 'text',
            'text': code,
            'hint': '请输入图中的字符',
        }
        answer = {'code': code.lower()}
        ttl = self._resolve_ttl((context or {}).get('config', {}), 180)
        return payload, answer, ttl

    def _generate_arithmetic(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        a, b = random.randint(1, 9), random.randint(1, 9)
        operator = random.choice(['+', '-'])
        expression = f'{a} {operator} {b}'
        result = a + b if operator == '+' else a - b
        payload = {
            'type': 'arithmetic',
            'expression': expression,
            'hint': '请输入算术题的答案',
        }
        answer = {'result': result}
        ttl = self._resolve_ttl((context or {}).get('config', {}), 180)
        return payload, answer, ttl

    def _generate_slider(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        offset = random.randint(20, 80)
        payload = {
            'type': 'slider',
            'image': '/static/captcha/slider-bg.png',
            'piece': '/static/captcha/slider-piece.png',
            'hint': '拖动滑块完成拼图',
        }
        answer = {'offset': offset}
        ttl = self._resolve_ttl((context or {}).get('config', {}), 240)
        return payload, answer, ttl

    def _generate_grid(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        targets = sorted(random.sample(range(9), 3))
        payload = {
            'type': 'grid',
            'question': '请选择所有的猫咪',
            'gridSize': 9,
            'images': [f'/static/captcha/grid/{i}.png' for i in range(9)],
        }
        answer = {'indexes': targets}
        ttl = self._resolve_ttl((context or {}).get('config', {}), 240)
        return payload, answer, ttl

    def _generate_behavior(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        required_steps = random.randint(3, 5)
        payload = {
            'type': 'behavior',
            'requiredSteps': required_steps,
            'hint': '按照提示轨迹拖动完成验证',
        }
        answer = {'completed': True, 'minSteps': required_steps}
        ttl = self._resolve_ttl((context or {}).get('config', {}), 240)
        return payload, answer, ttl

    def _generate_email(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        context = context or {}
        config = context.get('config', {})
        request_data = context.get('request', {})

        target_email = self._resolve_email_target(request_data, config)
        if not target_email:
            raise CaptchaGenerationError('邮箱地址未配置，无法发送验证码')

        code = self._random_digits(6)
        ttl = self._resolve_ttl(config, 300)
        self._send_email_code(target_email, code, ttl, config)

        payload = {
            'type': 'email',
            'maskedEmail': mask_email(target_email),
            'hint': '验证码已发送至邮箱，请查收',
        }
        answer = {'code': code}
        return payload, answer, ttl

    def _generate_sms(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        context = context or {}
        config = context.get('config', {})
        request_data = context.get('request', {})

        target_phone = self._resolve_phone_target(request_data, config)
        if not target_phone:
            raise CaptchaGenerationError('手机号未配置，无法发送验证码')

        code = self._random_digits(6)
        ttl = self._resolve_ttl(config, 300)
        self._send_sms_code(target_phone, code, ttl, config)

        payload = {
            'type': 'sms',
            'maskedPhone': mask_phone(target_phone),
            'hint': '验证码已发送至手机，请注意查收短信',
        }
        answer = {'code': code}
        return payload, answer, ttl

    def _generate_voice(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        context = context or {}
        config = context.get('config', {})
        request_data = context.get('request', {})

        target_phone = self._resolve_phone_target(request_data, config)
        if not target_phone:
            raise CaptchaGenerationError('手机号未配置，无法发送语音验证码')

        code = self._random_digits(6)
        ttl = self._resolve_ttl(config, 300)
        call_sid = self._send_voice_code(target_phone, code, ttl, config)

        payload = {
            'type': 'voice',
            'maskedPhone': mask_phone(target_phone),
            'hint': '系统正在拨打语音电话，请注意接听并输入验证码',
            'callSid': call_sid,
        }
        answer = {'code': code}
        return payload, answer, ttl

    def _generate_invisible(self, context: dict | None = None) -> Tuple[dict, dict, int]:
        context = context or {}
        config = context.get('config', {})
        honeypot_name = config.get('honeypot_name', 'contact_number')
        min_duration = float(config.get('min_duration', 2))

        payload = {
            'type': 'invisible',
            'honeypotName': honeypot_name,
            'minVisibleSeconds': min_duration,
        }
        answer = {'honeypot': '', 'minDuration': min_duration}
        ttl = self._resolve_ttl(config, 120)
        return payload, answer, ttl
    # endregion

    # region verifiers
    def _default_verify(self, expected: dict, actual: dict) -> bool:
        return expected == actual

    def _verify_text(self, expected: dict, actual: dict) -> bool:
        if not actual:
            return False
        return expected.get('code', '').lower() == str(actual.get('code', '')).lower()

    def _verify_arithmetic(self, expected: dict, actual: dict) -> bool:
        try:
            return int(expected.get('result')) == int(actual.get('result'))
        except (TypeError, ValueError):
            return False

    def _verify_slider(self, expected: dict, actual: dict) -> bool:
        try:
            return abs(float(actual.get('offset')) - float(expected.get('offset'))) <= 5
        except (TypeError, ValueError):
            return False

    def _verify_grid(self, expected: dict, actual: dict) -> bool:
        expected_indexes = sorted(expected.get('indexes', []))
        actual_indexes = sorted(actual.get('indexes', []))
        return expected_indexes == actual_indexes

    def _verify_behavior(self, expected: dict, actual: dict) -> bool:
        if not actual.get('completed'):
            return False
        try:
            actual_steps = int(actual.get('steps', expected.get('minSteps', 0)))
        except (TypeError, ValueError):
            actual_steps = 0
        try:
            required_steps = int(expected.get('minSteps', 0))
        except (TypeError, ValueError):
            required_steps = 0
        return actual_steps >= required_steps

    def _verify_email(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_sms(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_voice(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_invisible(self, expected: dict, actual: dict) -> bool:
        honeypot_ok = actual.get('honeypot', '') == expected.get('honeypot', '')
        try:
            duration = float(actual.get('duration', 0))
        except (TypeError, ValueError):
            duration = 0.0
        try:
            min_duration = float(expected.get('minDuration', 0))
        except (TypeError, ValueError):
            min_duration = 0.0
        return honeypot_ok and duration >= min_duration
    # endregion

    # region helpers
    def _normalize_answer(self, answer: Any) -> dict:
        if answer is None:
            return {}
        if isinstance(answer, dict):
            return answer
        if isinstance(answer, (list, tuple)):
            return {'indexes': list(answer)}
        if isinstance(answer, str):
            try:
                parsed = json.loads(answer)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {'indexes': parsed}
                return {'value': parsed}
            except json.JSONDecodeError:
                return {'code': answer}
        return {'value': answer}

    def _get_enabled_type(self, type_name: str) -> CaptchaType | None:
        try:
            return CaptchaType.objects.get(type_name=type_name, enabled=True)
        except CaptchaType.DoesNotExist:
            return None

    def _load_config(self, captcha_type: CaptchaType | None) -> dict:
        if not captcha_type or not captcha_type.config_json:
            return {}
        try:
            config = json.loads(captcha_type.config_json)
            return config if isinstance(config, dict) else {}
        except json.JSONDecodeError:
            logger.warning('验证码类型 %s 的配置不是有效的 JSON', captcha_type.type_name)
            return {}

    def _resolve_ttl(self, config: dict, default: int) -> int:
        ttl_value = config.get('ttl') if isinstance(config, dict) else None
        if ttl_value is None:
            return default
        try:
            ttl = int(ttl_value)
            return ttl if ttl > 0 else default
        except (TypeError, ValueError):
            return default

    def _random_digits(self, length: int) -> str:
        return ''.join(random.choices(string.digits, k=length))

    def _resolve_email_target(self, request_data: dict, config: dict) -> str | None:
        email = (
            request_data.get('email')
            or request_data.get('target_email')
            or config.get('email')
            or config.get('target_email')
        )
        username = request_data.get('username')
        if not email and username:
            try:
                from accounts.models import User  # local import to avoid circular dependency

                email = User.objects.filter(username=username).values_list('email', flat=True).first()
            except Exception:  # pragma: no cover - defensive guard
                logger.exception('根据用户名 %s 查询邮箱失败', username)
        return email

    def _resolve_phone_target(self, request_data: dict, config: dict) -> str | None:
        phone = (
            request_data.get('phone')
            or request_data.get('mobile')
            or request_data.get('target_phone')
            or config.get('phone')
            or config.get('mobile')
            or config.get('target_phone')
        )
        if not phone:
            test_number = getattr(settings, 'TEST_PHONE_NUMBER', '')
            phone = test_number or None
        return phone

    def _send_email_code(self, email: str, code: str, ttl: int, config: dict) -> None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
        if not from_email or not getattr(settings, 'EMAIL_HOST', ''):
            raise CaptchaGenerationError('邮件服务未正确配置，请联系管理员')

        subject = config.get('subject', '验证码验证')
        template = config.get('template', '您的验证码是 {code}，请在 {ttl} 秒内完成验证。')
        message = template.format(code=code, ttl=ttl)
        try:
            send_mail(subject, message, from_email, [email])
        except Exception as exc:  # pragma: no cover - 网络依赖
            logger.exception('发送邮件验证码失败: %s', exc)
            raise CaptchaGenerationError('邮件发送失败，请稍后重试') from exc

    def _get_twilio_client(self) -> tuple[Client, str]:
        if Client is None:
            raise CaptchaGenerationError('未安装 Twilio SDK，无法发送短信或语音验证码')
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        if not account_sid or not auth_token or not from_number:
            raise CaptchaGenerationError('Twilio 配置不完整，请联系管理员')
        return Client(account_sid, auth_token), from_number

    def _send_sms_code(self, phone: str, code: str, ttl: int, config: dict) -> None:
        client, from_number = self._get_twilio_client()
        template = config.get('template', '您的验证码是 {code}，有效期 {ttl} 秒。')
        message = template.format(code=code, ttl=ttl)
        try:
            client.messages.create(body=message, from_=from_number, to=phone)
        except TwilioException as exc:  # pragma: no cover - 网络依赖
            logger.exception('发送短信验证码失败: %s', exc)
            raise CaptchaGenerationError('短信发送失败，请稍后重试') from exc

    def _send_voice_code(self, phone: str, code: str, ttl: int, config: dict) -> str:
        client, from_number = self._get_twilio_client()
        digits = ' '.join(code)
        template = config.get('voice_text', '您的验证码是 {digits} 。请在 {ttl} 秒内完成输入。')
        voice_text = template.format(digits=digits, ttl=ttl)
        twiml = f'<Response><Say language="zh-CN">{voice_text}</Say></Response>'
        try:
            call = client.calls.create(twiml=twiml, to=phone, from_=from_number)
        except TwilioException as exc:  # pragma: no cover - 网络依赖
            logger.exception('拨打语音验证码失败: %s', exc)
            raise CaptchaGenerationError('语音验证码发送失败，请稍后重试') from exc
        return getattr(call, 'sid', '')
    # endregion


__all__ = ['CaptchaService', 'CaptchaGenerationError']
