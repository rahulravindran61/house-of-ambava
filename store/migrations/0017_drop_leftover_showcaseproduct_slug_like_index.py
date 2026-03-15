from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_order_cancellation_reason_order_cancelled_at'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP INDEX IF EXISTS store_showcaseproduct_slug_378f72cd_like;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
