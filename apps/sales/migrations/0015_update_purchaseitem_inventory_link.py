# Generated migration to update PurchaseItem model with proper Inventory link
# This migration:
# 1. Adds ForeignKey to Inventory
# 2. Removes product_name CharField
# 3. Adds timestamp fields
# 4. Updates metadata and adds indexes

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0014_purchaseitem'),
        ('stock_management', '0001_initial'),  # Ensure stock_management migrations run first
    ]

    operations = [
        # Add new fields to PurchaseItem
        migrations.AddField(
            model_name='purchaseitem',
            name='inventory',
            field=models.ForeignKey(
                help_text='Inventory item being purchased',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='purchase_items',
                to='stock_management.inventory'
            ),
        ),
        
        # Add timestamp fields
        migrations.AddField(
            model_name='purchaseitem',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='purchaseitem',
            name='modified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        
        # Update quantity field to DecimalField
        migrations.AlterField(
            model_name='purchaseitem',
            name='quantity',
            field=models.DecimalField(
                decimal_places=2,
                help_text='Quantity of the product',
                max_digits=10
            ),
        ),
        
        # Remove product_name field (after data migration if needed)
        migrations.RemoveField(
            model_name='purchaseitem',
            name='product_name',
        ),
        
        # Update table name and add indexes
        migrations.AlterModelOptions(
            name='purchaseitem',
            options={
                'ordering': ['-created'],
                'verbose_name': 'Purchase Item',
                'verbose_name_plural': 'Purchase Items'
            },
        ),
        
        migrations.AlterModelTable(
            name='purchaseitem',
            table='purchase_item',
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='purchaseitem',
            index=models.Index(fields=['bill'], name='purchase_item_bill_idx'),
        ),
        migrations.AddIndex(
            model_name='purchaseitem',
            index=models.Index(fields=['inventory'], name='purchase_item_inventory_idx'),
        ),
    ]
