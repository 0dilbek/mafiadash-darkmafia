from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('bot', '0007_cinema_models')]
    operations = [
        migrations.CreateModel(
            name='CinemaViewer',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('first_seen_at', models.DateTimeField(auto_now_add=True)),
                ('last_seen_at', models.DateTimeField()),
            ],
            options={'db_table': 'cinema_viewer', 'managed': False},
        ),
    ]
