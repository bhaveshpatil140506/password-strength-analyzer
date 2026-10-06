from django.db import migrations, models
import django.db.models.deletion


def create_table_if_missing(apps, schema_editor):
    if 'api_sessions' not in schema_editor.connection.introspection.table_names():
        # This table may already exist when the PHP schema installer was run.
        # The model is imported only while applying this migration, after app
        # loading, so the operation remains safe for either backend setup order.
        from analyzer.models import ApiSession
        schema_editor.create_model(ApiSession)


def drop_table_if_present(apps, schema_editor):
    if 'api_sessions' in schema_editor.connection.introspection.table_names():
        from analyzer.models import ApiSession
        schema_editor.delete_model(ApiSession)


class Migration(migrations.Migration):
    dependencies = [('analyzer', '0001_initial')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(create_table_if_missing, drop_table_if_present)],
            state_operations=[migrations.CreateModel(
                name='ApiSession',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('token_hash', models.CharField(max_length=64, unique=True)),
                    ('expires_at', models.DateTimeField()),
                    ('created_at', models.DateTimeField(auto_now_add=True)),
                    ('user', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='api_sessions', to='analyzer.user')),
                ],
                options={'db_table': 'api_sessions'},
            )],
        ),
    ]
