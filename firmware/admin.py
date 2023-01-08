from django.contrib import admin


from .models import Brand, AssociatedName, Product, FG, Version


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "fg_count"]

    def fg_count(self, obj):
        return str(len(obj.fgs.all()))

class FGAdmin(admin.ModelAdmin):
    list_display = ["number", "count", "products"]

    def count(self, obj):
        product_list = obj.product_set.all()
        return str(len(product_list))


    def products(self, obj):
        product_list = obj.product_set.all()
        return [product.name for product in product_list]

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


admin.site.register(Brand)
admin.site.register(AssociatedName, AssociatedNameAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(FG, FGAdmin)
admin.site.register(Version, VersionAdmin)