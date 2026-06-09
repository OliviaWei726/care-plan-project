from django.urls import path
from . import views

urlpatterns = [
    path("",          views.order_form,   name="form"),
    path("submit/",   views.submit_order, name="submit"),
    path("orders/",   views.order_list,   name="orders"),
]
