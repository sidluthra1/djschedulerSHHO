# On a fresh database the squashed migration 0008 never drops is_djteacher, and 0011
# only removes it from Django's state, so the NOT NULL column lingers and breaks every
# Profile insert. Drop it if it is still there; databases that already lost it are untouched.

from django.db import migrations


def drop_is_djteacher(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = [c.name for c in connection.introspection.get_table_description(cursor, 'users_profile')]
    if 'is_djteacher' in columns:
        schema_editor.execute('ALTER TABLE users_profile DROP COLUMN is_djteacher')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_alter_profile_role_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_is_djteacher, migrations.RunPython.noop),
    ]
