from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0009_payment'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='invoice',
            name='invoice_payment_327947_idx',
        ),
        migrations.RemoveIndex(
            model_name='salesorder',
            name='sales_order_payment_ca014c_idx',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='paid_amount',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='payment_method',
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='payment_status',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='paid_amount',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='payment_method',
        ),
        migrations.RemoveField(
            model_name='salesorder',
            name='payment_status',
        ),
    ]
