# Generated by Django 3.2 on 2020-10-22 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userAccount', '0004_alter_course_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='bio',
            field=models.TextField(default='default bio'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='useraccount',
            name='major',
            field=models.CharField(default='CS', max_length=50),
            preserve_default=False,
        ),
    ]