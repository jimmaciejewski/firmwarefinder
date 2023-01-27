from django.shortcuts import render, redirect, reverse
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

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
        # If we are searching, search current and discontinued products
        for product in Product.objects.all():
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        queryset = Product.objects.filter(id__in=products_with_versions).order_by('name')
        # To search the read_me in the firmware versions -- first get the fgs with the search result

        search_query = SearchQuery(query)
        search_vector = SearchVector('read_me') + SearchVector('name')
        versions_fgs_list = Version.objects.annotate(search=search_vector).filter(search=search_query).values_list('fgs')

        # versions_fgs = Version.objects.filter(read_me__icontains=query).values_list('fgs')
        # versions_names_fgs = Version.objects.filter(name__icontains=query).values_list('fgs')
        # # versions_fgs = Version.objects.annotate(search=SearchVector('read_me', 'name')).filter(search=query).values_list('fgs')

        queryset = queryset.filter(Q(fgs__in=versions_fgs_list)).distinct()
            
        # Q(name__icontains=query) | 
        #                            Q(associated_names__name__icontains=query) |
        #                            Q(fgs__number__icontains=query) |
        
    
        # Then check if the fgs are in the product
        vector = (SearchVector('name', weight='A') +
                  SearchVector('associated_names', weight='B') +
                  SearchVector('fgs__number', weight='C')
                  )
        search_query = SearchQuery(query)
        rate = SearchRank(vector, query)
        products = queryset.annotate(rate=rate).annotate(search=vector).distinct('name', 'rate').order_by('-rate', 'name')


        # search_vector = SearchVector('name', weight='A') + SearchVector('associated_names__name', weight='B') + SearchVector('fgs__number')
        
        # products = queryset.annotate(
        #     search=search_vector, rank=SearchRank(search_vector, search_query)).filter(search=search_query).distinct('rank', 'name').order_by('-rank', 'name')
         




        #    Q(fgs__in=versions_fgs)).distinct()

        
        # vector = SearchVector('name')
        
        # products = queryset.annotate(rank=SearchRank(vector, search_query)).order_by('-rank')

        # products = queryset.filter(Q(name__icontains=query) | 
        #                            Q(associated_names__name__icontains=query) |
        #                            Q(fgs__number__icontains=query) |
        #                            Q(fgs__in=versions_fgs) |
        #                            Q(fgs__in=versions_names_fgs)).distinct()
    else:
        # Regular list here, just need to limit it to current or discontinued 
        for product in Product.objects.filter(discontinued=discontinued):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        products = Product.objects.filter(discontinued=discontinued, id__in=products_with_versions).order_by('name')

    html = render_to_string(
        template_name="firmware/prod_list.html",
        context={"products": products}
    )

    data_dict = {"html_from_view": html}
    return JsonResponse(data=data_dict, safe=False)
