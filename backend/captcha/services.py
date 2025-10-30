import json
import random
import string
from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from django.db import transaction

from .models import CaptchaChallenge, CaptchaType


@dataclass
class CaptchaGenerator:
    description: str
    generator: Callable[[], Tuple[dict, dict, int]]
    default_ttl: int = 180


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

    def generate_challenge(self, *, client_ip: str, user_agent: str = '', requested_type: str | None = None) -> CaptchaChallenge:
        type_name = requested_type or self.get_default_type()
        if type_name not in self._registry or not CaptchaType.objects.filter(type_name=type_name, enabled=True).exists():
            type_name = self.get_default_type()
        generator = self._registry[type_name]
        payload, answer, ttl = generator.generator()
        challenge = CaptchaChallenge.create(
            type_name,
            json.dumps(payload, ensure_ascii=False),
            json.dumps(answer, ensure_ascii=False),
            client_ip=client_ip,
            user_agent=user_agent,
            ttl_seconds=ttl,
        )
        return challenge

    def validate_and_consume(self, *, token: str, user_answer, client_ip: str) -> tuple[bool, str, str | None]:
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
                CaptchaType.objects.update_or_create(
                    type_name=type_name,
                    defaults={
                        'description': generator.description,
                        'enabled': True,
                        'config_json': json.dumps({'ttl': generator.default_ttl}, ensure_ascii=False),
                        'is_default': type_name == 'text',
                    },
                )
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
    def _generate_text(self) -> Tuple[dict, dict, int]:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        payload = {
            'type': 'text',
            'text': code,
            'hint': '请输入图中的字符',
        }
        answer = {'code': code.lower()}
        return payload, answer, 180

    def _generate_arithmetic(self) -> Tuple[dict, dict, int]:
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
        return payload, answer, 180

    def _generate_slider(self) -> Tuple[dict, dict, int]:
        offset = random.randint(20, 80)
        payload = {
            'type': 'slider',
            'image': '/static/captcha/slider-bg.png',
            'piece': '/static/captcha/slider-piece.png',
            'hint': '拖动滑块完成拼图',
        }
        answer = {'offset': offset}
        return payload, answer, 240

    def _generate_grid(self) -> Tuple[dict, dict, int]:
        targets = random.sample(range(9), 3)
        payload = {
            'type': 'grid',
            'question': '请选择所有的猫咪',
            'gridSize': 9,
            'images': [f'/static/captcha/grid/{i}.png' for i in range(9)],
        }
        answer = {'indexes': sorted(targets)}
        return payload, answer, 240

    def _generate_behavior(self) -> Tuple[dict, dict, int]:
        required_steps = random.randint(3, 5)
        payload = {
            'type': 'behavior',
            'requiredSteps': required_steps,
            'hint': '按照提示轨迹拖动完成验证',
        }
        answer = {'completed': True, 'minSteps': required_steps}
        return payload, answer, 240

    def _generate_email(self) -> Tuple[dict, dict, int]:
        code = ''.join(random.choices(string.digits, k=6))
        payload = {
            'type': 'email',
            'maskedEmail': '******@example.com',
            'hint': '验证码已发送至邮箱',
        }
        answer = {'code': code}
        return payload, answer, 300

    def _generate_sms(self) -> Tuple[dict, dict, int]:
        code = ''.join(random.choices(string.digits, k=6))
        payload = {
            'type': 'sms',
            'maskedPhone': '138****8888',
            'hint': '验证码已发送至手机',
        }
        answer = {'code': code}
        return payload, answer, 300

    def _generate_voice(self) -> Tuple[dict, dict, int]:
        code = ''.join(random.choices(string.digits, k=6))
        payload = {
            'type': 'voice',
            'audioUrl': '/static/captcha/voice-code.mp3',
            'hint': '请听取语音播报的数字并输入',
        }
        answer = {'code': code}
        return payload, answer, 300

    def _generate_invisible(self) -> Tuple[dict, dict, int]:
        payload = {
            'type': 'invisible',
            'honeypotName': 'contact_number',
            'minVisibleSeconds': 2,
        }
        answer = {'honeypot': '', 'minDuration': 2}
        return payload, answer, 120
    # endregion

    # region verifiers
    def _default_verify(self, expected, actual) -> bool:
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
        return bool(actual.get('completed')) and int(actual.get('steps', expected.get('minSteps', 0))) >= int(expected.get('minSteps', 0))

    def _verify_email(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_sms(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_voice(self, expected: dict, actual: dict) -> bool:
        return expected.get('code') == actual.get('code')

    def _verify_invisible(self, expected: dict, actual: dict) -> bool:
        return actual.get('honeypot', '') == expected.get('honeypot', '') and float(actual.get('duration', 0)) >= float(expected.get('minDuration', 0))
    # endregion

    def _normalize_answer(self, answer) -> dict:
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


__all__ = ['CaptchaService']
