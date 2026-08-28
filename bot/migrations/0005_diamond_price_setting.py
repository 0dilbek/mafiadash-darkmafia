from django.db import migrations, models


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS diamondpricesetting (
    id BIGSERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    amount BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT diamondpricesetting_amount_nonnegative CHECK (amount >= 0)
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0004_chat_role_order'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_TABLE,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='DiamondPriceSetting',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('key', models.CharField(max_length=100, unique=True)),
                        ('amount', models.BigIntegerField()),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'db_table': 'diamondpricesetting',
                        'managed': False,
                    },
                ),
            ],
        ),
    ]
