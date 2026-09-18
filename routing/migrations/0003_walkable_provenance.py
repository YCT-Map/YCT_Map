from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("routing", "0002_locationnetworkanchor")]

    operations = [
        migrations.AddField(
            model_name="walkablenode", name="source_type",
            field=models.CharField(choices=[("SYNTHETIC", "Synthetic fixture"), ("OSM", "OpenStreetMap"), ("MANUAL", "YCT Map manual")], default="SYNTHETIC", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(model_name="walkablenode", name="source_reference", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="walkablenode", name="source_version", field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="walkablenode", name="source_timestamp", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(
            model_name="walkablesegment", name="source_type",
            field=models.CharField(choices=[("SYNTHETIC", "Synthetic fixture"), ("OSM", "OpenStreetMap"), ("MANUAL", "YCT Map manual")], default="SYNTHETIC", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(model_name="walkablesegment", name="source_reference", field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name="walkablesegment", name="source_version", field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="walkablesegment", name="source_timestamp", field=models.DateTimeField(blank=True, null=True)),
        migrations.AlterField(
            model_name="walkablenode", name="source_type",
            field=models.CharField(choices=[("SYNTHETIC", "Synthetic fixture"), ("OSM", "OpenStreetMap"), ("MANUAL", "YCT Map manual")], default="MANUAL", max_length=20),
        ),
        migrations.AlterField(
            model_name="walkablesegment", name="source_type",
            field=models.CharField(choices=[("SYNTHETIC", "Synthetic fixture"), ("OSM", "OpenStreetMap"), ("MANUAL", "YCT Map manual")], default="MANUAL", max_length=20),
        ),
    ]
