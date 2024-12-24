from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('trains/', views.train_list_view, name='train_list'),
    path('train/<int:train_id>/', views.train_detail_view, name='train_detail'),  # For regular users
    path('details/', views.train_details_list_view, name='train_details_list'),
    path('logout/', views.logout_view, name='logout'),
    # Change this URL to avoid conflict with Django admin
    path('manage/train/<int:train_id>/', views.train_detail_admin_view, name='train_detail_admin'),  # For admin users
    #
    path('manage_data/', views.delete_train_data, name='delete_train_data'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
