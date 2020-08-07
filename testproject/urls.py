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
from   threading                 import Timer
import json
import pymysql
import hashlib

conn = pymysql.connect(host="127.0.0.1",
                       user="root",
                       password="",
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

@api_view(['POST'])
def user_auth(request):
    username        = request.POST.get("username")
    password_hashed = hashlib.md5(str.encode( request.POST.get("password") )).digest()

    try:
        cursor.execute( "SELECT type, user_id FROM users WHERE username='" + username + "' and password=%s;", (password_hashed))
        conn.commit()

        result = cursor.fetchone()

        if result is None:
            return Response({
                "success": False,
                "error": "invalid credentials"
            })

        return Response({
            "success"   : True,
            "status"    : "",
            "user_type" : result[0],
            "user_id"   : result[1]
        })
    except pymysql.Error as e:
        return Response({
            "success" : False,
            "error"   : "%d: %s" % (e.args[0], e.args[1])
        })

def randomly_assign_order(order_id, dummy):

    cursor.execute( "SELECT * FROM orders WHERE order_id="+str(order_id)+" AND partner_id is NULL AND status='created'")
    conn.commit()

    result = cursor.fetchone()

    if result is None:
        print("order already assigned")
    else:
        cursor.execute( "SELECT user_id FROM users WHERE type='partner'")
        conn.commit()

        all_partners = []

        for row in cursor.fetchall():
            all_partners.append(row[0])

        if len(all_partners) == 0:
            cursor.execute("UPDATE orders SET status='cancelled' WHERE order_id="+ str(order_id))
            conn.commit()

        else:
            cursor.execute("UPDATE orders SET status='partner_assigned', partner_id="+str(all_partners[0])+" WHERE order_id="+ str(order_id))
            conn.commit()


@api_view(['POST', 'GET'])
def order_create_and_get_details(request):
    if request.method == 'POST':
        client_id        = int(request.POST.get("client_id"))
        pickup_address   = request.POST.get("pick_up_address")
        drop_address     = request.POST.get("drop_address")
        item_description = request.POST.get("item_description")
        item_title       = request.POST.get("item_title")

        try:
            cursor.execute( "INSERT INTO orders(client_id, pickup_address, drop_address, item_description, partner_id) VALUES(" + str(client_id) + ",'" + pickup_address + "', '" + drop_address + "', '" + json.dumps({"desc": item_description, "title": item_title}) + "', NULL)")
            conn.commit()

            Timer(30.0, randomly_assign_order, (cursor.lastrowid, " ")).start()

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
            cursor.execute("SELECT * FROM orders WHERE order_id=" + request.GET.get('order_id', -1))
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
                "item_description" : json.loads(result[6])['desc'],
                "item_title"       : json.loads(result[6])['title'],
                "state"            : result[5],
                "success"          : True,
                "status"           : ""
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

    cursor.execute("SELECT * FROM orders WHERE partner_id="+str(partner_id))
    conn.commit()

    all_orders = []

    for order in cursor.fetchall():
        all_orders.append({
            "order_id"         : order[0],
            "client_id"        : order[1],
            "partner_id"       : order[2],
            "pick_up_address"  : order[3],
            "drop_address"     : order[4],
            "item_description" : json.loads(order[6])['desc'],
            "item_title"       : json.loads(order[6])['title'],
            "state"            : order[5],
        })

    return Response(all_orders)

@api_view(['GET'])
def client_details(request):
    client_id = int(request.GET.get('client_id', None))

    cursor.execute("SELECT * FROM orders WHERE client_id="+str(client_id))
    conn.commit()

    all_orders = []

    for order in cursor.fetchall():
        all_orders.append({
            "order_id"         : order[0],
            "client_id"        : order[1],
            "partner_id"       : order[2],
            "pick_up_address"  : order[3],
            "drop_address"     : order[4],
            "item_description" : json.loads(order[6])['desc'],
            "item_title"       : json.loads(order[6])['title'],
            "state"            : order[5],
        })

    return Response(all_orders)

@api_view(['GET'])
def testQR(request):
    qr = request.GET.get('identifier', None)

    if qr == "1":
        return Response({
            "success": True,
            "status": "Order Successfully Delivered",
        })
    else:
        return Response({
            "success": False,
            "status": "Order Delivery Rejected! Invalid credentials!",
        })


@api_view(['GET'])
def getQR(request):
    order_id = request.GET.get('order_id', None)


    return Response({
        "identifier": "1"
    })


@api_view(['GET'])
def available_orders(request):
    cursor.execute("SELECT * FROM orders WHERE partner_id is NULL AND status='created';")
    conn.commit()

    all_orders = []

    for order in cursor.fetchall():
        all_orders.append({
            "order_id"         : order[0],
            "client_id"        : order[1],
            "partner_id"       : order[2],
            "pick_up_address"  : order[3],
            "drop_address"     : order[4],
            "item_description" : json.loads(order[6])['desc'],
            "item_title"       : json.loads(order[6])['title'],
            "state"            : order[5],
        })

    return Response(all_orders)

@api_view(['GET'])
def partner_accept_order(request):
    partner_id = request.GET.get('partner_id')
    order_id   = request.GET.get('order_id')

    try:
        cursor.execute("UPDATE orders SET partner_id="+partner_id+" WHERE order_id="+order_id+" status='partner_assigned';")
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


urlpatterns = [
    url(r'^hello/$'                       , hello_world),

    # common
    url(r'^users/auth/$'                  , user_auth),
    url(r'^users/$'                       , user_create),

    # delivery side
    url(r'^partner/orders/$'              , partner_details),
    url(r'^partner/orders/accept/$'       , partner_accept_order),
    url(r'^orders/available/$'            , available_orders),
    url(r'^orders/getQR/$'                , getQR),

    # client side
    url(r'^orders/$'                      , order_create_and_get_details),
    url(r'^orders/(?P<order_id>[0-9]+)/$' , change_order_state),
    url(r'^client/orders/$'               , client_details),
    url(r'^orders/testQR/$'               , testQR),
]
