from django.shortcuts import render, redirect, reverse
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
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


class ProductSearchView(ListView):
    model = Product
    context_object_name = 'products'
    ordering = ['name']
    discontinued = False

    def get_context_data(self, **kwargs):
        context = super(ProductSearchView, self).get_context_data(**kwargs)
        if self.discontinued:
            context['active'] = "discontinued"
        else:
            context['active'] = "products"
        context['search'] = self.request.GET.get('q')
        if context['search'] is not None:
            # Since we search both current and discontinued product, don't highlight the NAV bar when results are shown...
            context['active'] = ""
        return context
    
    def get_queryset(self):
        """My attempt at getting the intersection of product fg and version fg 
           I suspect this could be written more efficiently
        """
        products_with_versions = []
        query = self.request.GET.get('q')
        
        if query is not None:
            # If we are searching, search current and discontinued products
            for product in Product.objects.all():
                if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                    products_with_versions.append(product.id)
            queryset = Product.objects.filter(id__in=products_with_versions).order_by('name')
            # To search the read_me in the firmware versions -- first get the fgs with the search result
            versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
            versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')
        
            # Then check if the fgs are in the product
            return queryset.filter(Q(name__icontains=query) | 
                                   Q(fgs__number__icontains=query) |
                                   Q(fgs__in=versions_fgs) |
                                   Q(fgs__in=versions_names_fgs))
        else:
            # Regular list here, just need to limit it to current or discontinued 
            for product in Product.objects.filter(discontinued=self.discontinued):
                if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                    products_with_versions.append(product.id)
            return Product.objects.filter(discontinued=self.discontinued, id__in=products_with_versions).order_by('name')

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

def products_search(request):
    products_with_versions = []
    query = request.GET.get('q')
    
    if query is not None:
        # If we are searching, search current and discontinued products
        for product in Product.objects.all():
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(id__in=products_with_versions).order_by('name')
        # To search the read_me in the firmware versions -- first get the fgs with the search result
        versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')
    
        # Then check if the fgs are in the product
        products = queryset.filter(Q(name__icontains=query) | 
                                Q(fgs__number__icontains=query) |
                                Q(fgs__in=versions_fgs) |
                                Q(fgs__in=versions_names_fgs))
    else:
        # # Regular list here, just need to limit it to current or discontinued 
        # for product in Product.objects.filter(discontinued=discontinued):
        #     if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
        #         products_with_versions.append(product.id)
        # return Product.objects.filter(discontinued=discontinued, id__in=products_with_versions).order_by('name')
        products = Product.objects.all()
    html = render_to_string(
        template_name="firmware/prod_list.html",
        context={"products": products}
    )

    data_dict = {"html_from_view": html}
    return JsonResponse(data=data_dict, safe=False)
