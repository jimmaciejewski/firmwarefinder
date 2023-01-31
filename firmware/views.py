from django.shortcuts import render
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils import timezone

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

import operator
from functools import reduce

from .models import Brand, Product, Version, FG, SubscribedUser
from .forms import SubscribeForm

def thanks(request):
    return render(request, "firmware/thanks.html")

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
    
    def get_queryset(self):
        """We populate the page with ajax
        """
        return Product.objects.none()

class ProductDetailView(DetailView):
    model = Product


class SubscribeForm(FormView):
    template_name = 'firmware/subscribe.html'
    form_class = SubscribeForm
    success_url = '/thanks/'

    def get_context_data(self, **kwargs):
        context = super(SubscribeForm, self).get_context_data(**kwargs)
        context['active'] = "subscribe"
        return context

    def form_valid(self, form):
        new_subscriber, created = SubscribedUser.objects.get_or_create(email=form.cleaned_data['email'], name=form.cleaned_data['name'])
        if not created:
            print('already exists')
            return
        return super().form_valid(form)

def products_search(request):
    products_with_versions = []
    query = request.GET.get('q')
    if request.GET.get('discontinued') == 'false':
        discontinued = False
    else:
        discontinued = True

    
    if query:
        query = query.strip()
        # If we are searching, search current and discontinued products
        for product in Product.objects.all():
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(id__in=products_with_versions).order_by('name')

        versions_readme_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')

        # Trying again... here is the plan
        # We need to modify the search passed in to better match the products we are searching for
        # Example 1: query="DX RX"
        #   Here we should search for "DX RX", additionally search for "DXRX" "DX-RX"
        # Example 2: query="DX-RX"
        #   Here we should search for "DX-RX", additionally search for "DXRX" "DX RX"

        query_list = [query]
        if "-" in query:
            query_list.append(query.replace('-', ''))
            query_list.append(query.replace('-', ' '))
        if " " in query:
            query_list.append(query.replace(' ', ''))
            query_list.append(query.replace(' ', '-'))
            ''
        # Take the results of all these queries search add them together, and distinct() 
        field_list = ['name__icontains', 'associated_names__name__icontains', 'fgs__number__icontains']
        q_set = [Q(fgs__in=versions_readme_fgs),Q(fgs__in=versions_names_fgs)]
        for item in query_list:
            for field in field_list:
                q_set.append(Q(**{field: item}))
        combined_query = reduce(operator.or_, q_set)
        queryset = queryset.filter(combined_query).distinct()
        # Then we want to rank them based on quality of match using annotate
        search_query = SearchQuery(query)
        vector = SearchVector('name') + SearchVector('fgs__number')
        rate = SearchRank(vector, search_query)
        products = queryset.annotate(rate=rate).annotate(search=vector).distinct('name', 'rate').order_by('-rate', 'name')

        if not products:
            # Lets log any searches that don't find anything...
            try:
                with open('failed_searches.txt', 'a') as f:
                    f.write(f'{timezone.now().isoformat()} :: {query}\r</br>')
            except Exception as error:
                print(f"Unable to log query: {error}")

    else:
        # Regular list here, just need to limit it to current or discontinued 
        for product in Product.objects.filter(discontinued=discontinued):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        products = Product.objects.filter(discontinued=discontinued, id__in=products_with_versions).order_by('name')


    context= {"products": products}
    client_ip = get_client_ip(request)
    if client_ip == '127.0.0.1':
        context['show_local'] = True
    else:
        print(f"From ip: {client_ip}")


    html = render_to_string(
        template_name="firmware/prod_list.html",
        context=context
    )

    data_dict = {"html_from_view": html}
    return JsonResponse(data=data_dict, safe=False)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
