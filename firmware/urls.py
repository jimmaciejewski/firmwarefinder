from django.urls import path

from . import views

app_name = 'firmware'

urlpatterns = [
    path('', views.welcome, name='home'),
    path('lines', views.lines, name='lines'),
    # path('', views.tree, name='tree'),
    path('sites', views.BrandListView.as_view(), name='brand-list'),
    path('brand/<int:pk>/', views.BrandDetailView.as_view(), name='brand-detail'),
    path('products', views.ProductSearchView.as_view(), name='product-list'),
    # path('products/', views.ProductListView.as_view(), name='product-list'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    # path('firmwares', views.FirmwareListView.as_view(), name='firmware-list'),
    # path('firmware/<int:pk>/', views.FirmwareDetailView.as_view(), name='firmware-detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]