from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("locations", "0005_remove_development_demo_locations"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="is_checkpoint",
            field=models.BooleanField(
                default=False,
                help_text="Emphasize this place as a prominent wayfinding landmark.",
                verbose_name="Show as map checkpoint",
            ),
        ),
    ]
