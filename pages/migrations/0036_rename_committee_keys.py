from django.db import migrations


RENAMES = {
    'eduunlocked': 'ea',
    'nextgen': 'ype',
    'young_artists': 'yac',
}


def rename_forward(apps, schema_editor):
    MemberRole = apps.get_model('pages', 'MemberRole')
    for old, new in RENAMES.items():
        MemberRole.objects.filter(committee=old).update(committee=new)


def rename_backward(apps, schema_editor):
    MemberRole = apps.get_model('pages', 'MemberRole')
    for old, new in RENAMES.items():
        MemberRole.objects.filter(committee=new).update(committee=old)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0035_alter_initiative_director'),
    ]

    operations = [
        migrations.RunPython(rename_forward, rename_backward),
    ]
