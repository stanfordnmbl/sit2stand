# Generated by Django 3.0.8 on 2021-03-10 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motionlab', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='recordid',
            field=models.CharField(max_length=32),
        ),
    ]