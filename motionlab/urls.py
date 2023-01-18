"""gaitlab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('thankyou/<str:mode>/', views.thankyou, name='thankyou'),
    path('beforestart/', views.beforestart, name='beforestart'),
    path('consent/', views.consent, name='consent'),
    path('rerunall/', views.rerun_all, name='rerun_all'),
    path('readiness/<int:page>/', views.readiness, name='readiness'),
    path('form/', views.form, name='form'),
    path('validate/<slug:slug>/', views.validate, name='validate'),
    
    path('analysis/<slug:slug>/', views.analysis, name='analysis'),
    path('analysis/<slug:slug>/json/', views.analysis_json, name='analysis_json'),
    path('annotation/<int:id>/', views.annotation_update, name='annotation'),
    path('admin/', admin.site.urls),

    path('contact/', views.contact, name='contact'),
    path('application/', views.application, name='application'),
    path('success/', views.success, name='success'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('terms/', views.terms, name='terms'),

    path('private/', views.private, name='private'),
    path('academic/', views.private, name='private'),
    path('healthai/', views.private, name='private'),
    path('whish/', views.private, name='private'),
    path('reset/', views.reset, name='reset'),
]
