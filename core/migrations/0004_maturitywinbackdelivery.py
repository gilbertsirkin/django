from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_campaignannouncement"),
        ("investments", "0006_alter_dailyroipayout_unique_together_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaturityWinbackDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipient_email", models.EmailField(max_length=254)),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("subject", models.CharField(max_length=255)),
                (
                    "investment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="maturity_winback_delivery",
                        to="investments.userinvestment",
                    ),
                ),
            ],
            options={
                "ordering": ["-sent_at"],
                "indexes": [models.Index(fields=["recipient_email", "-sent_at"], name="core_maturi_recipie_8d0c9b_idx")],
            },
        ),
    ]
