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
from   rest_framework.response   import Response
from   rest_framework.decorators import api_view
from   django.conf.urls          import url, include
from   django.http               import QueryDict
import json
import pymysql
import hashlib

conn = pymysql.connect(host="127.0.0.1",
                       user="root",
                       password="root",
                       db="onboarding")
cursor = conn.cursor()


@api_view(['GET', 'POST'])
def hello_world(request):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})


@api_view(['POST'])
def user_create(request):
    username        = request.POST.get("username")
    password_hashed = hashlib.md5(str.encode( request.POST.get("password") )).digest()
    user_type       = request.POST.get("user_type")

    try:
        cursor.execute( "INSERT INTO users(username, password, type) VALUES('" + username + "',%s, '" + user_type + "')", (password_hashed))
        conn.commit()

        return Response({
            "success" : True,
            "status"  : "User Created Successfully",
        })
    except pymysql.Error as e:
        return Response({
            "success" : False,
            "error"   : "%d: %s" % (e.args[0], e.args[1])
        })


@api_view(['POST', 'GET'])
def order_create_and_get_details(request):
    if request.method == 'POST':
        client_id        = int(request.POST.get("client_id"))
        pickup_address   = request.POST.get("pick_up_address")
        drop_address     = request.POST.get("drop_address")
        item_description = request.POST.get("item_description")

        try:
            cursor.execute( "INSERT INTO orders(client_id, pickup_address, drop_address, item_description, partner_id) VALUES(" + str(client_id) + ",'" + pickup_address + "', '" + drop_address + "', '" + item_description + "', NULL)")
            conn.commit()

            return Response({
                "success" : True,
                "status"  : "Order Created Successfully",
            })
        except pymysql.Error as e:
            return Response({
                "success" : False,
                "error"   : "%d: %s" % (e.args[0], e.args[1])
            })

    elif request.method == 'GET':
        try:
            cursor.execute("SELECT * FROM orders WHERE order_id=" +
                           request.GET.get('order_id', -1))
            conn.commit()

            result = cursor.fetchone()

            if result is None:
                return Response({
                    "success" : False,
                    "error"   : "No such order exists!"
                })

            return Response({
                "order_id"         : request.GET.get('order_id', -1),
                "client_id"        : result[1],
                "partner_id"       : result[2],
                "pick_up_address"  : result[3],
                "drop_address"     : result[4],
                "item_description" : result[6],
                "state"            : result[5],
            })
        except pymysql.Error as e:
            return Response({
                "success" : False,
                "error"   : "%d: %s" % (e.args[0], e.args[1])
            })


@api_view(['PUT'])
def change_order_state(request, order_id):
    order_id = int(order_id)
    newState = json.loads(request.body)['status']

    try:
        cursor.execute("UPDATE orders SET status='"+newState+"' WHERE order_id="+ str(order_id))
        conn.commit()

        return Response({
            "success" : True,
            "status"  : "Order State updated"
        })
    except pymysql.Error as e:
        return Response({
            "success" : False,
            "error"   : "%d: %s" % (e.args[0], e.args[1])
        })


@api_view(['GET'])
def partner_details(request):
    partner_id = int(request.GET.get('partner_id', None))

    try:
        cursor.execute("SELECT * FROM orders WHERE partner_id="+str(partner_id))
        conn.commit()

        all_orders = []

        for order in cursor.fetchall():
            all_orders.append({
                "order_id"         : request.GET.get('order_id', -1),
                "client_id"        : order[1],
                "partner_id"       : order[2],
                "pick_up_address"  : order[3],
                "drop_address"     : order[4],
                "item_description" : order[6],
                "state"            : order[5],
            })

        return Response(all_orders)

    except pymysql.Error as e:
        return Response({
            "success" : False,
            "error"   : "%d: %s" % (e.args[0], e.args[1])
        })


urlpatterns = [
    url(r'^hello/$'                       , hello_world),
    url(r'^users/$'                       , user_create),
    url(r'^orders/$'                      , order_create_and_get_details),
    url(r'^orders/(?P<order_id>[0-9]+)/$' , change_order_state),
    url(r'^partner/orders/$'              , partner_details),
]
