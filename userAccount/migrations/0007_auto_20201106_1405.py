# Generated by Django 3.1.1 on 2020-11-06 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userAccount', '0006_auto_20201104_1753'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useraccount',
            old_name='name',
            new_name='first_name',
        ),
        migrations.AddField(
            model_name='useraccount',
            name='last_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]