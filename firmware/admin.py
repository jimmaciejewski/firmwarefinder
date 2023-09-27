from django.contrib import admin


from .models import Brand, AssociatedName, Product, FG, Version, Subscriber


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "store_firmware_versions_locally", "fg_count"]

    def fg_count(self, obj):
        return str(len(obj.fgs.all()))

class FGAdmin(admin.ModelAdmin):
    list_display = ["number", "related_product_count", "products", "related_version_count", "versions"]

    def related_product_count(self, obj):
        product_list = obj.product_set.all()
        return str(len(product_list))

    def related_version_count(self, obj):
        version_list = obj.version_set.all()
        return str(len(version_list))

    def products(self, obj):
        product_list = obj.product_set.all()
        return [product.name for product in product_list]

    def versions(self, obj):
        version_list = obj.version_set.all()
        return [version.name for version in version_list]

class AssociatedNameAdmin(admin.ModelAdmin):
    list_display = ["name", "count", "products"]

    def count(self, obj):
        product_list = obj.product_set.all()
        return str(len(product_list))

    def products(self, obj):
        product_list = obj.product_set.all()
        return [product.name for product in product_list]


@admin.action(description='Refresh readme')
def refresh_readme(modeladmin, request, queryset):
    for version in queryset.all():
        version.read_me = version.get_release_notes()
        version.save()

class VersionAdmin(admin.ModelAdmin):
    list_display = ["name", "number", "hotfix", "downloaded", "fg_count"]
    actions = [refresh_readme]

    def downloaded(self, obj):
        return bool(obj.local_file)

    def fg_count(self, obj):
        return str(len(obj.fgs.all()))

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["user", 'get_email_address', "send_email", "send_email_even_if_none_found"]

    def get_email_address(self, obj):
        return obj.user.email
    
    get_email_address.admin_order_field = 'user'
    get_email_address.short_description = 'Email Address'


admin.site.register(Brand)
admin.site.register(AssociatedName, AssociatedNameAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(FG, FGAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Subscriber, SubscriberAdmin)

