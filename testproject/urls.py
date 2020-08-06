"""testproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf.urls import url, include
from django.http import QueryDict
import json


@api_view(['GET','POST'])
def hello_world(request):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})

@api_view(['POST'])
def user_create(request):
    request.POST.get("user_type")
    request.POST.get("username")
    request.POST.get("password")

    print(request.POST)

    return Response({"status": "User Created Successfully",})

@api_view(['POST', 'GET'])
def order_create_and_get_details(request):
    if request.method == 'POST':
        request.POST.get("client_id")
        request.POST.get("pick_up_address")
        request.POST.get("drop_address")
        request.POST.get("item_description")

        print(request.POST)

        return Response({"status": "Order Created Successfully",})
    elif request.method == 'GET':
        print(request.GET)

        return Response({
            "order_id": request.GET.get('order_id', None),
            "client_id": 1,
            "partner_id": None,
            "pick_up_address": "ABCD",
            "drop_address": "ABCD",
            "item_description": "Some description of items",
            "state": "created",
        })

@api_view(['PUT'])
def change_order_state(request, order_id):
    print(order_id)
    print(json.loads(request.body))
    return Response({"status": "Order State updated"})

@api_view(['GET'])
def partner_details(request):
    request.GET.get('partner_id', None)

    print(request.GET)

    return Response([{
        "order_id": request.GET.get('partner_id', None),
        "client_id": 1,
        "partner_id": None,
        "pick_up_address": "ABCD",
        "drop_address": "ABCD",
        "item_description": "Some description of items",
        "state": "created",
    }])


urlpatterns = [
    url(r'^hello/$', hello_world),
    url(r'^users/$', user_create),
    url(r'^orders/$', order_create_and_get_details),
    url(r'^orders/(?P<order_id>[0-9]+)/$', change_order_state),
    url(r'^partner/orders/$', partner_details),
]
