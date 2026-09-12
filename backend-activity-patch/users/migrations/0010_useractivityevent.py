from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_profile_telegram_chat_id_profile_telegram_link_token_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserActivityEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(blank=True, db_index=True, max_length=128)),
                ("page_url", models.CharField(max_length=500)),
                ("page_path", models.CharField(db_index=True, max_length=255)),
                ("page_title", models.CharField(blank=True, max_length=255)),
                ("visited_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "users_activity_event",
                "ordering": ["-visited_at"],
                "indexes": [
                    models.Index(fields=["user", "-visited_at"], name="users_activ_user_id_94ac32_idx"),
                    models.Index(fields=["user", "page_path", "-visited_at"], name="users_activ_user_id_a58d93_idx"),
                ],
            },
        ),
    ]
