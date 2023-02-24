from django.urls import path

from . import views

app_name = 'firmware'

urlpatterns = [
    path('', views.ProductSearchView.as_view(discontinued=False), name='product-list'),
    path('discontinued-products', views.ProductSearchView.as_view(discontinued=True), name='discontinued-product-list'),\

    # path('lines', views.lines, name='lines'),
    # path('sites', views.BrandListView.as_view(), name='brand-list'),
    # path('brand/<int:pk>/', views.BrandDetailView.as_view(), name='brand-detail'),
    # path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # path('subscribe/', views.subscribe, name='subscribe'),
    path("register", views.register_request, name="register"),
    path('login', views.login_page, name='login'),
    path('profile', views.profile, name='profile'),
    path('products-search', views.products_search, name='products-search'),
    path('thanks/', views.thanks, name='thanks'),
    path('activate-user/<int:id>/', views.activate_user, name='activate-user'),

]
