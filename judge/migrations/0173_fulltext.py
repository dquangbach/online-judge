from django.db import migrations


def create_fulltext_indexes(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute(
        "SELECT COUNT(1) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = 'judge_problem' AND index_name = 'code_name_index'"
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "CREATE FULLTEXT INDEX code_name_index ON judge_problem (code, name)"
        )

    cursor.execute(
        "SELECT COUNT(1) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = 'judge_contest' AND index_name = 'key_name_index'"
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "CREATE FULLTEXT INDEX key_name_index ON judge_contest (`key`, name)"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("judge", "0172_index_rating"),
    ]

    operations = [
        migrations.RunPython(
            create_fulltext_indexes, reverse_code=migrations.RunPython.noop
        ),
    ]
