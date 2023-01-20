from django.shortcuts import render, redirect, reverse
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q


from .models import Brand, Product, Version, FG
from .forms import SubscribeForm

def welcome(request):
    return redirect("/products")

def lines(request):
    context = {}
    context['products'] = Product.objects.all()
    return render(request, 'firmware/lines.html', context)
    
class BrandListView(ListView):
    model = Brand

class BrandDetailView(DetailView):
    model = Brand


class DiscontinuedProductListView(ListView):
    model = Product
    context_object_name = 'products'
    ordering = ['name']

    def get_context_data(self, **kwargs):
        context = super(DiscontinuedProductListView, self).get_context_data(**kwargs)
        context['active'] = "discontinued"
        context['search'] = self.request.GET.get('q')
        return context

    def get_queryset(self):
        """My attempt at getting the intersection of product fg and version fg 
           I suspect this could be written more efficiently
        """
        products_with_versions = []
        for product in Product.objects.filter(discontinued=True):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(discontinued=True, id__in=products_with_versions).order_by('name')
        query = self.request.GET.get('q')
        if not query:
            return queryset
        # To search the read_me in the firmware versions -- first get the fgs with the search result
        versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')
        
        # Then check if the fgs are in the product
        products = queryset.filter(
            Q(name__icontains=query) | Q(fgs__number__icontains=query) | Q(fgs__in=versions_fgs) | Q(fgs__in=versions_names_fgs)
        )
        return products


class ProductSearchView(ListView):
    model = Product
    context_object_name = 'products'
    ordering = ['name']

    def get_context_data(self, **kwargs):
        context = super(ProductSearchView, self).get_context_data(**kwargs)
        context['active'] = "products"
        context['search'] = self.request.GET.get('q')
        return context
    
    def get_queryset(self):
        """My attempt at getting the intersection of product fg and version fg 
           I suspect this could be written more efficiently
        """
        products_with_versions = []
        for product in Product.objects.filter(discontinued=False):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(discontinued=False, id__in=products_with_versions).order_by('name')
        query = self.request.GET.get('q')
        if not query:
            return queryset
        # To search the read_me in the firmware versions -- first get the fgs with the search result
        versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')
        
        # Then check if the fgs are in the product
        products = queryset.filter(
            Q(name__icontains=query) | Q(fgs__number__icontains=query) | Q(fgs__in=versions_fgs) | Q(fgs__in=versions_names_fgs)
        )
        return products


class ProductDetailView(DetailView):
    model = Product


class SubscribeForm(FormView):
    template_name = 'firmware/subscribe.html'
    form_class = SubscribeForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super(SubscribeForm, self).get_context_data(**kwargs)
        context['active'] = "subscribe"
        return context

    def form_valid(self, form):
        return super().form_valid(form)


