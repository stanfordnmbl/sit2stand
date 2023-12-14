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
from django.urls import path, include, register_converter

from .converters import SlugsConverter

from . import views

register_converter(SlugsConverter, 'slugs')

urlpatterns = [
    path('', views.index, name='index'),
    path('thankyou/<str:mode>/', views.thankyou, name='thankyou'),
    path('beforestart/', views.beforestart, name='beforestart'),
    path('faq/', views.faq, name='faq'),
    path('consent/', views.consent, name='consent'),
    path('rerunall/', views.rerun_all, name='rerun_all'),
    path('readiness/<int:page>/', views.readiness, name='readiness'),
    path('assess/', views.assess, name='assess'),
    path('assess/self/', views.self_assess, name='self_assess'),
    path('assess/research/', views.for_researchers, name='for_researchers'),
    path('validate/<slug:slug>/', views.validate, name='validate'),
    path('validate_multiple/<slugs:slugs>/', views.validate_multiple, name='validate_multiple'),

    path('under_construction/', views.under_construction, name='under_construction'),

    path('assess/results/<slug:slug>/', views.analysis, name='analysis'),
    path('assess/results/<slug:slug>/json/', views.analysis_json, name='analysis_json'),
    path('assess/results/<slug:slug>/csv/', views.analysis_csv, name='analysis_csv'),
    path('assess/results/<slug:slug>/analysis_simple_csv/', views.analysis_simple_csv, name='analysis_simple_csv'),
    path('assess/multiple_results/<slugs:slugs>/', views.analysis_multiple, name='analysis_multiple'),
    path('annotation/<int:id>/', views.annotation_update, name='annotation'),
    path('admin/', admin.site.urls),

    # path('contact/', views.contact, name='contact'),
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

# Captcha
urlpatterns += [
    path('captcha/', include('captcha.urls')),
]