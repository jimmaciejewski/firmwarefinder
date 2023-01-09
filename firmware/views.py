from django.shortcuts import render
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q
from django.http import JsonResponse
import re
from django.core.mail import send_mail
from django.conf import settings
from .models import Brand, Product, Version, FG, SubscribedUser
from .forms import SubscribeForm

def welcome(request):
    return render(request, 'firmware/index.html')

def lines(request):
    context = {}
    context['products'] = Product.objects.all()
    return render(request, 'firmware/lines.html', context)
    
class BrandListView(ListView):
    model = Brand

class BrandDetailView(DetailView):
    model = Brand

class ProductListView(ListView):
    # paginate_by = 14
    model = Product
    context_object_name = 'products'
    ordering = ['name']

    def get_queryset(self):
        """My attempt at getting the intersection of product fg and version fg 
           I suspect this could be written more efficiently
        """
        products_with_versions = []
        for product in Product.objects.filter(discontinued=False):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(id__in=products_with_versions).order_by('name')
        return queryset

class ProductSearchView(ProductListView):
    
    def get_queryset(self):
        # Get the queryset however you usually would.  For example:
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if not query:
            return queryset
        # To search the read_me in the firmware versions -- first get the fgs with the search result
        versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        # Then check if the fgs are in the product
        products = queryset.filter(
            Q(name__icontains=query) | Q(fgs__number__icontains=query) | Q(fgs__in=versions_fgs)
        )
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('q')
        return context

class ProductDetailView(DetailView):
    model = Product


class SubscribeForm(FormView):
    template_name = 'firmware/subscribe.html'
    form_class = SubscribeForm
    success_url = '/'

    def form_valid(self, form):
        if form.is_valid():
            form.save()

        return super().form_valid(form)


