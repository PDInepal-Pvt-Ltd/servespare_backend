# Generated migration for Favorite model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock_management', '0001_initial'),
        ('carts', '0002_remove_cart_is_removed_remove_cartitem_is_removed_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(auto_now_add=True, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(auto_now=True, verbose_name='modified')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this favorite is still active')),
                ('inventory', models.ForeignKey(help_text='Inventory product added to favorites', on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='stock_management.inventory')),
                ('user', models.ForeignKey(help_text='User who added this to favorites', on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Favorite',
                'verbose_name_plural': 'Favorites',
                'db_table': 'favorites',
                'ordering': ['-created'],
            },
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['user', 'inventory'], name='favorites_user_invento_idx'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['user', '-created'], name='favorites_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=models.Index(fields=['is_active'], name='favorites_is_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='favorite',
            unique_together={('user', 'inventory')},
        ),
    ]
