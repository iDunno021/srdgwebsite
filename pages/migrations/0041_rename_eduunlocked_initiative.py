from django.db import migrations


def rename_initiative(apps, schema_editor):
    Initiative = apps.get_model('pages', 'Initiative')
    Initiative.objects.filter(title='EduUnlocked').update(title='Educational Advancement')


def reverse_rename(apps, schema_editor):
    Initiative = apps.get_model('pages', 'Initiative')
    Initiative.objects.filter(title='Educational Advancement').update(title='EduUnlocked')


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0040_aboutphoto'),
    ]

    operations = [
        migrations.RunPython(rename_initiative, reverse_rename),
    ]
