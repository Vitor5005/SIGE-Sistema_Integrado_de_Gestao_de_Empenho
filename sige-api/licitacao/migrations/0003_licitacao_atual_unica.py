from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licitacao', '0002_licitacao_atual'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE `licitacao_licitacao`
                ADD COLUMN `atual_unico` TINYINT
                    GENERATED ALWAYS AS (
                        CASE WHEN `atual` = 1 THEN 1 ELSE NULL END
                    ) STORED,
                ADD UNIQUE INDEX `uniq_licitacao_atual` (`atual_unico`);
            """,
            reverse_sql="""
                ALTER TABLE `licitacao_licitacao`
                DROP INDEX `uniq_licitacao_atual`,
                DROP COLUMN `atual_unico`;
            """,
        ),
    ]
