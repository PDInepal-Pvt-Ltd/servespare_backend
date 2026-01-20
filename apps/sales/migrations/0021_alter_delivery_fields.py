# Generated migration for delivery_state to delivery_province and adding delivery_district

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0020_bill_tax_amount_bill_tax_percentage_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='salesorder',
            name='delivery_state',
        ),
        migrations.AddField(
            model_name='salesorder',
            name='delivery_province',
            field=models.CharField(
                blank=True,
                help_text='Delivery province',
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='salesorder',
            name='delivery_district',
            field=models.CharField(
                blank=True,
                help_text='Delivery district',
                max_length=100,
                null=True,
            ),
        ),
    ]
