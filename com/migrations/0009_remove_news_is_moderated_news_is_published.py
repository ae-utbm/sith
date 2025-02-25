from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("com", "0008_alter_news_options_alter_newsdate_options_and_more")]

    operations = [
        migrations.RenameField(
            model_name="news", old_name="is_moderated", new_name="is_published"
        ),
        migrations.AlterField(
            model_name="news",
            name="is_published",
            field=models.BooleanField(default=False, verbose_name="is published"),
        ),
    ]
