from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail
from django.forms import inlineformset_factory

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

import requests
import os

import operator
from functools import reduce

from .models import Brand, Product, Version, FG, Subscriber
from .forms import ActivateUserForm, UserProfileForm, NewUserForm, SubscriberForm, LoginForm


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
        versions_numbers_fgs = Version.objects.filter(number__icontains=query.replace('v', '')).values_list('fgs')

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
        q_set = [Q(fgs__in=versions_readme_fgs),Q(fgs__in=versions_names_fgs),Q(fgs__in=versions_numbers_fgs)]
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
                    f.write(f'{timezone.now().isoformat()} :: {query}\r')
            except Exception as error:
                print(f"Unable to log query: {error}")

    else:
        # Regular list here, just need to limit it to current or discontinued 
        for product in Product.objects.filter(discontinued=discontinued):
            if Version.objects.filter(fgs__in=FG.objects.filter(product=product)):
                products_with_versions.append(product.id)
        products = Product.objects.filter(discontinued=discontinued, id__in=products_with_versions).order_by('name')


    context= {"products": products, "show_local": request.user.is_authenticated}

    html = render_to_string(
        template_name="firmware/prod_list.html",
        context=context
    )

    data_dict = {"html_from_view": html}
    return JsonResponse(data=data_dict, safe=False)


@staff_member_required(login_url='/accounts/login/', redirect_field_name='next')
def activate_user(request, id):
    activate_user = get_object_or_404(User, id=id)

    if request.method == "POST":
        form = ActivateUserForm(request.POST, instance=activate_user)
        if form.is_valid():
            form.save()
            context = {'new_user': activate_user}
            content = render_to_string(
                template_name="email/user_welcome_email.html",
                context=context
            )
            send_mail(
                subject="Welcome to Firmware Monitoring",
                message=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[activate_user.email],
                html_message=content
            )
            return render(request, 'registration/thanks.html', {'title': f'Thanks for activating!', 'message': f'You have helped out {activate_user.email}'})
    else:
        form = ActivateUserForm(instance=activate_user)

    return render(request, 'registration/activate_user.html', {'form': form, 'activate_user': activate_user})


class LoginView(auth_views.LoginView):
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'sitekey': settings.CAPTCHA_SITEKEY})

    def form_valid(self, form):
        recaptcha_response = self.request.POST.get('g-recaptcha-response')
        data = {'secret': settings.CAPTCHA_SECRET_KEY, 'response': recaptcha_response}
        result = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        if result.status_code == 200 and result.json()['success']:
             return super().form_valid(form)
        else:
            form.add_error(None, "You need to prove you are not a robot!")
            return super().form_invalid(form)

@login_required(login_url='/login')
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        form2 = SubscriberForm(request.POST, instance=request.user.subscriber)
        if form2.is_valid():
            form2.save()
        if form.is_valid():
            form.save()
            messages.info(request, f"Profile updated")
            return redirect('/profile')
    else:
        form = UserProfileForm(instance=request.user)
        form2 = SubscriberForm(instance=request.user.subscriber)

    return render(request, 'registration/profile_change_form.html', {'form': form, 'form2': form2, 'user': request.user})


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            recaptcha_response = request.POST.get('g-recaptcha-response')
            data = {'secret': settings.CAPTCHA_SECRET_KEY, 'response': recaptcha_response}
            result = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            if result.status_code == 200 and result.json()['success']:
                user = form.save()
                user.is_active = False
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                if user.last_name:
                    user.username = f"{user.first_name.lower()}.{user.last_name.lower()}"
                else:
                    user.username = user.first_name
                new_subscriber = Subscriber(user=user)
                new_subscriber.save()
                user.save()
                for staff_user in User.objects.filter(is_staff=True):
                    context = {'name': staff_user.username, 'new_user': user}
                    content = render_to_string(
                        template_name="email/admin_user_verification_email.html",
                        context=context
                    )
                    send_mail(
                        subject="New User Request",
                        message=content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[staff_user.email],
                        html_message=content
                    )
                return render(request, 'registration/thanks.html', {'title': f'Thanks for subscribing!', 'message': f'You will receive an email when your account is activated'})
            else:
                form.add_error(None, "You need to prove you are not a robot!")
                messages.error(request, "You need to prove you are not a robot!")
    else:
        form = NewUserForm()
    return render (request=request, template_name="registration/register.html", context={"form":form, 'active': 'register', 'sitekey': settings.CAPTCHA_SITEKEY})


def login_page(request):

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
            if user:
                if user.is_active:
                    login(request, user)
                    next = request.POST.get('next')
                    if next:
                        return redirect(next)
                    else:
                        return redirect('firmware:product-list')
            else:
                messages.error(request, 'Email or password is not correct')
    else:
        form = LoginForm()
    return render(request, template_name="registration/login.html", context={'form': form, 'active': 'login'})


@login_required(login_url='/login')
def download_local_file(request, id):
    version = get_object_or_404(Version, id=id)
    if os.path.exists(version.local_file.path):
        with open(version.local_file.path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(version.local_file.path)
            return response
    raise Http404
