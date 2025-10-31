from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('captcha', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='captchatype',
            name='type_name',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='captchatype',
            name='description',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='captchatype',
            name='config_json',
            field=models.TextField(blank=True, default='{}'),
        ),
        migrations.AlterField(
            model_name='captchatype',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='captchatype',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]
