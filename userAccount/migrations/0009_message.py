# Generated by Django 3.1.1 on 2020-11-19 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userAccount', '0008_auto_20201111_2050'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unread', models.BooleanField()),
                ('content', models.CharField(max_length=10000)),
                ('sequence', models.IntegerField()),
                ('from_requester', models.BooleanField()),
                ('buddies', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userAccount.buddies')),
            ],
        ),
    ]