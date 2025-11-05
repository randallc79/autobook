from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('results/<int:job_id>/', views.results, name='results'),
    path('logs/<int:job_id>/', views.logs, name='logs'),
]
