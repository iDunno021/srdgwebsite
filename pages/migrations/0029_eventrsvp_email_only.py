from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0028_alter_eventrsvp_unique_together_eventrsvp_member_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eventrsvp',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='eventrsvp',
            name='member',
        ),
        migrations.AddField(
            model_name='eventrsvp',
            name='email',
            field=models.EmailField(max_length=254, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='eventrsvp',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterUniqueTogether(
            name='eventrsvp',
            unique_together={('event', 'email')},
        ),
    ]
