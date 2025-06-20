# Generated by Django 4.2 on 2025-06-16 13:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_dashboard', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='supplementorder',
            name='approved_by',
            field=models.ForeignKey(blank=True, help_text='Admin who approved the order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='supplementorder',
            name='cart_items',
            field=models.ManyToManyField(to='admin_dashboard.cartitem'),
        ),
        migrations.AddField(
            model_name='supplementorder',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='ratesetting',
            unique_together={('role', 'effective_date')},
        ),
        migrations.AddField(
            model_name='paymentlog',
            name='payment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='admin_dashboard.payment'),
        ),
        migrations.AddField(
            model_name='paymentlog',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payment',
            name='milk_collections',
            field=models.ManyToManyField(blank=True, related_name='payments', to='admin_dashboard.milkcollection'),
        ),
        migrations.AddField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='milkcollection',
            name='collection_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='milk_collections', to='admin_dashboard.collectionpoint'),
        ),
        migrations.AddField(
            model_name='milkcollection',
            name='collector',
            field=models.ForeignKey(limit_choices_to={'role': 'collector'}, on_delete=django.db.models.deletion.PROTECT, related_name='milk_collections', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='milkcollection',
            name='farmer',
            field=models.ForeignKey(limit_choices_to={'role': 'farmer'}, on_delete=django.db.models.deletion.PROTECT, related_name='milk_supplies', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='supplement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_dashboard.supplement'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
