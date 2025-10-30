from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CaptchaType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_name', models.CharField(max_length=100, unique=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('config_json', models.TextField(blank=True)),
                ('is_default', models.BooleanField(default=False)),
                ('enabled', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '验证码类型',
                'verbose_name_plural': '验证码类型',
            },
        ),
        migrations.CreateModel(
            name='CaptchaChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('payload', models.TextField()),
                ('answer', models.TextField()),
                ('client_ip', models.CharField(max_length=64)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('validated', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': '验证码挑战',
                'verbose_name_plural': '验证码挑战',
            },
        ),
        migrations.AddIndex(
            model_name='captchachallenge',
            index=models.Index(fields=['token'], name='captcha_ch_token_fa8112_idx'),
        ),
        migrations.AddIndex(
            model_name='captchachallenge',
            index=models.Index(fields=['type'], name='captcha_ch_type_96c2c0_idx'),
        ),
    ]
