from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("routing", "0008_pathsurvey_active_capture_seconds_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="entrancenetworkanchor",
            name="connector_geometry",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
