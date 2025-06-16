from django.contrib import admin
from .models import RateSetting, MilkCollection, Payment, CollectionPoint
from .models import Supplement, CartItem, SupplementOrder


@admin.register(RateSetting)
class RateSettingAdmin(admin.ModelAdmin):
    list_display = ('role', 'rate_per_litre', 'effective_date')
    list_filter = ('role',)
    ordering = ('-effective_date',)
    search_fields = ('role',)


@admin.register(CollectionPoint)
class CollectionPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_person', 'contact_phone')
    search_fields = ('name', 'location', 'contact_person')


@admin.register(MilkCollection)
class MilkCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'date_collected', 'farmer', 'collector', 'quantity_litres',
        'amount_payable_to_farmer', 'commission_payable_to_collector', 'collection_point', 'is_paid'
    )
    list_filter = ('date_collected', 'collector', 'farmer', 'is_paid', 'collection_point')
    search_fields = ('farmer__username', 'collector__username')
    readonly_fields = (
        'farmer_rate_at_collection', 'collector_rate_at_collection',
        'amount_payable_to_farmer', 'commission_payable_to_collector',
        'created_at', 'updated_at'
    )
    ordering = ('-date_collected',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'gross_amount', 'net_amount', 'status', 'date_paid')
    list_filter = ('status', 'date_paid')
    search_fields = ('user__username', 'user__email', 'remarks')
    autocomplete_fields = ['user', 'milk_collections']
    readonly_fields = ('gross_amount', 'farmer_deduction', 'collector_deduction', 'net_amount')

    fieldsets = (
        ('User & Collections', {
            'fields': ('user', 'milk_collections')
        }),
        ('Financials', {
            'fields': ('gross_amount', 'farmer_deduction', 'collector_deduction', 'net_amount')
        }),
        ('Payment Details', {
            'fields': ('method', 'status', 'remarks', 'date_paid')
        }),
    )
    
@admin.register(Supplement)
class SupplementAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('-id',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'supplement', 
        'quantity', 
        'price_at_order', 
        'discount_applied', 
        'added_on'
    )
    list_filter = ('added_on', 'discount_applied')
    search_fields = ('user__username', 'supplement__name')
    ordering = ('-added_on',)


class CartItemInline(admin.TabularInline):
    model = SupplementOrder.cart_items.through
    extra = 0
    verbose_name = "Cart Item"
    verbose_name_plural = "Cart Items"
    readonly_fields = ('cartitem',)

    def cartitem(self, instance):
        return f"{instance.cartitem.quantity} × {instance.cartitem.supplement.name}"


@admin.register(SupplementOrder)
class SupplementOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('user__username', 'remarks')
    ordering = ('-created_at',)
    inlines = [CartItemInline]
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'cart_items', 'total_price', 'payment_method', 'status', 'remarks', 'created_at')
        }),
    )