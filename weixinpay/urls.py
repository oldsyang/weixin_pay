"""weixinpay URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from exa import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^code/', views.get_image),
    url(r'^test/weixin/$', views.notify_url_event),
    url(r'^test/weixin/search_order/', views.search_order),
    url(r'^test/weixin/close_order/', views.close_order),
    url(r'^test/weixin/refund_order/', views.refund_order),
    url(r'^test/weixin/search_refund_order/', views.search_refund_order),
    url(r'^$', views.home),

]
