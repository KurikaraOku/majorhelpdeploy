# Generated by Django 5.1.4 on 2025-04-18 21:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MajorHelp', '0002_alter_university_slug'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='majorreview',
            unique_together={('user', 'major')},
        ),
    ]
