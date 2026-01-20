# Generated migration for barcode field update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_management', '0008_alter_party_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='barcode',
            field=models.CharField(
                blank=True,
                help_text='Barcode for scanning (alphanumeric only, max 50 characters)',
                max_length=50,
                null=True,
                unique=True
            ),
        ),
    ]
