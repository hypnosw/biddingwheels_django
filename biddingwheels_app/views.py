import datetime
import json
import os
import dotenv
from pymysql import DatabaseError, IntegrityError
from .models import User
from django.db import connection
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, HttpResponse, redirect
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from datetime import datetime
from django.contrib.auth import logout
import logging

# 配置日志记录器
logging.basicConfig(level=logging.DEBUG)  # 设置日志级别为DEBUG

# 获取logger对象
logger = logging.getLogger(__name__)

load_dotenv()
# Create your views here.


def server_start(request):
    return HttpResponse("Server started successfully. \n Make sure to double"
                        "check environment variables for allowed hosts.")


def admin_reports(request):
    try:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT 
                c.listid as Listing_id, c.image, c.make as Make, c.model as Model, 
                u.username as Seller, u.user_id as SellerId, 
                with_listid.description, with_listid.Reporter, with_listid.Reporter_id
            FROM
                CarListing c
                INNER JOIN (
                    SELECT 
                        r.listing_id as Lister, r.description, 
                        u.username as Reporter, r.reporter_id as Reporter_id
                    FROM 
                        biddingwheels.ListingReport r
                        INNER JOIN User u ON u.user_id = r.reporter_id
                ) as with_listid ON c.listid = with_listid.Lister
                INNER JOIN User u ON u.user_id = c.sellerid
        ''')
        rows = cursor.fetchall()


        data = [
            {
                'ListId': row[0],
                'Image': row[1],
                'Make': row[2],
                'Model': row[3],
                'Seller': row[4],
                'SellerId': row[5],
                'Description': row[6],
                'Reporter': row[7],
                'ReporterId': row[8]
            }
            for row in rows
        ]
        return JsonResponse(data, safe=False)

    except Exception:
        return HttpResponse(status=404)

def all_listings(request):
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            cl.listid, cl.licenseNumber, cl.engineSerialNumber, cl.make, cl.model, 
            cl.year, cl.mileage, cl.city, cl.color, cl.additionalFeatures, 
            cl.description, cl.startingPrice, cl.biddingDeadline, cl.highestBid, 
            cl.highestBidHolder, u.username, cl.image
        FROM 
            CarListing cl
            JOIN User u ON cl.sellerID = u.user_id
    ''')

    rows = cursor.fetchall()

    data = [
        {
            'listid': row[0],
            'licenseNumber': row[1],
            'engineSerialNumber': row[2],
            'make': row[3],
            'model': row[4],
            'year': row[5],
            'mileage': row[6],
            'city': row[7],
            'color': row[8],
            'additionalFeatures': row[9],
            'description': row[10],
            'startingPrice': row[11],
            'biddingDeadline': row[12],
            'highestBid': row[13],
            'highestBidHolder': row[14],
            'sellerUsername': row[15],
            'image': row[16]
        }
        for row in rows
    ]

    return JsonResponse(data, safe=False)

def website_stats(request):
    class Stats:
        def __init__(self, dates, sales):
            self.dates = dates
            self.sales = sales

        def serialize(self):
            return{
                "dates": self.dates,
                "sales": self.sales,
            }

    stat = Stats(["Mar-01", "Mar-02", "Mar-03", "Mar-04", "Mar-05"],
                 [34, 60, 23, 55, 69])
    stat_json = json.dumps(stat.serialize())
    if stat_json:
        return HttpResponse(stat_json)
    else:
        return HttpResponse(status=404)


def detail_page(request, listid):
    cursor = connection.cursor()
    try:
        cursor.execute('''
            SELECT 
                cl.listid, cl.licenseNumber, cl.engineSerialNumber, cl.make, cl.model, 
                cl.year, cl.mileage, cl.city, cl.color, cl.additionalFeatures, 
                cl.description, cl.startingPrice, cl.biddingDeadline, cl.highestBid, 
                cl.highestBidHolder, u.username, b.username AS highestBidHolderUsername, cl.image
            FROM 
                CarListing cl
                JOIN User u ON cl.sellerID = u.user_id
                LEFT JOIN User b ON cl.highestBidHolder = b.user_id
            WHERE 
                cl.listid = %s
        ''', [listid])

        row = cursor.fetchone()

        if row:
            car_data = {
                'listid': row[0],
                'licenseNumber': row[1],
                'engineSerialNumber': row[2],
                'make': row[3],
                'model': row[4],
                'year': row[5],
                'mileage': row[6],
                'city': row[7],
                'color': row[8],
                'additionalFeatures': row[9],
                'description': row[10],
                'startingPrice': row[11],
                'biddingDeadline': row[12],
                'highestBid': row[13],
                'highestBidHolder': row[14],
                'sellerUsername': row[15],
                'highestBidHolderUsername': row[16] if row[16] else 'No highest bid holder',
                'image': row[17]
            }

            return JsonResponse(car_data)
        else:
            return HttpResponse(status=404)
    finally:
        cursor.close()

@csrf_exempt
def post_listing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            values = (
                data.get('sellerID', 1),  # Default value set to 1
                data.get('licenseNumber', ''),
                data.get('engineSerialNumber', ''),
                data.get('make', ''),
                data.get('model', ''),
                data.get('year', 0),
                data.get('mileage', 0),
                data.get('city', ''),
                data.get('color', ''),
                data.get('additionalFeatures', ''),
                data.get('description', ''),
                data.get('startingPrice', 0),
                data.get('biddingDeadline', ''),
                -1,  # Assuming -1 is the default value for highestBid and highestBidHolder
                1,  # Assuming 1 is the default value for highestBidHolder
                data.get('image', '')
            )

            # Execute the SQL query.
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO CarListing
                    (sellerID, licenseNumber, engineSerialNumber, make, model, year, mileage, city, color, additionalFeatures, description, startingPrice, biddingDeadline, highestBid, highestBidHolder, image)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, STR_TO_DATE(%s, '%%Y-%%m-%%dT%%H:%%i:%%sZ'), %s, %s, %s)
                ''', values)

            return JsonResponse({'status': 'success', 'message': 'Listing created successfully'})

        except Exception as e:
            # Handle other exceptions
            return JsonResponse({'status': 'error', 'message': 'An error occurred: ' + str(e)})
    else:
        # If the method is not POST, return an error
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def submit_bid(request):
    if not request.method == "POST":
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({"success": False, "message": "User not logged in"}, status=401)
    
    try:
        data = json.loads(request.body)
        bid = float(data.get("bid"))
        listing_id = data.get("listing_id")
        user_id = request.session.get('user_id') 

        with connection.cursor() as cursor:
            # Fetch the current highest bid
            cursor.execute('SELECT highestBid FROM CarListing WHERE listid = %s', [listing_id])
            row = cursor.fetchone()
            if row:
                current_highest_bid = row[0]
                if bid > current_highest_bid:
                    # Update the bid
                    cursor.execute('UPDATE CarListing SET highestBid = %s, highestBidHolder = %s WHERE listid = %s', 
                               [bid, user_id, listing_id])
                    return JsonResponse({"success": True, "message": "Bid placed successfully"})
                else:
                    return JsonResponse({"success": False, "message": "Bid must be higher than the current highest bid"}, status=400)
            else:
                return JsonResponse({"success": False, "message": "Car listing not found"}, status=404)

    except KeyError:
        return JsonResponse({"success": False, "message": "Missing required data"}, status=400)
    except ValueError:
        return JsonResponse({"success": False, "message": "Invalid bid value"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"An unexpected error occurred: {e}"}, status=500)


@csrf_exempt
def post_report(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')
    if request.method == 'POST':
        if not request.session.get('user_id'):
            return JsonResponse({"error": "User not logged in"}, status=401)
        
        try:
            data = json.loads(request.body)
            reporter_id = request.session.get('user_id')
            description = data['description']
            listing_id = int (data['listing_id'])
            submit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # submit_time = datetime.now()

            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO ListingReport (reporter_id, submit_time, description, listing_id) 
                    VALUES (%s, %s, %s, %s)
                ''', [reporter_id, submit_time, description, listing_id])
            
            return JsonResponse({'message': 'Report submitted successfully'})

        except KeyError as e:
            return HttpResponseBadRequest(f'Missing field: {e}')
        except ValueError as e:
            # This will catch issues like conversion errors
            return HttpResponseBadRequest(f'Invalid data: {e}')
        except DatabaseError as e:
            # Specific handling for database errors
            return HttpResponseBadRequest(f'Database error: {e}')
        except Exception as e:
            # Catch-all for any other exceptions
            return HttpResponseBadRequest(f'An unexpected error occurred: {e}')

# 用户注册
@csrf_exempt  # 禁用 CSRF 防护，以便前端可以发送 POST 请求
def signup(request):
    if request.method == 'POST':
        # 从前端拿用户名和密码
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        #检查一下用户名是否已经存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        # 创建一个user然后存到数据库user表里
        user = User.objects.create(username=username, password=password, role='normal')

        # 注册成功
        response = JsonResponse({'message': 'User created successfully'})
        response['Access-Control-Allow-Origin'] = 'http://localhost:3000'  # 允许跨域请求
        response['Access-Control-Allow-Credentials'] = True  # 允许携带凭据
    else:
        # 如果不是 POST 请求，返回错误消息
        response = JsonResponse({'error': 'Invalid request method'}, status=405)

    return response

#登录
@csrf_exempt
def login(request):
    logger.debug('Login request received')  # 打印调试信息

    if request.method == 'OPTIONS':
        logger.debug('Handling preflight request')  # 打印调试信息
        response = JsonResponse({'message': 'Preflight request handled successfully'})
        response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response['Access-Control-Allow-Credentials'] = True
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Methods'] = 'POST'
        return response

    elif request.method == 'POST':
        logger.debug('Handling POST request')  # 打印调试信息
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error('User does not exist')  # 打印错误信息
            response = JsonResponse({'error': 'Username does not exist'}, status=401)
            response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            response['Access-Control-Allow-Credentials'] = True
            return response
        
        print("输入的密码:", password)
        print("数据库中存储的密码:", user.password)

        # 验证密码是否匹配
        if password != user.password:
            logger.error('Invalid password')  # 打印错误信息
            response = JsonResponse({'error': 'Invalid password'}, status=401)
            response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            response['Access-Control-Allow-Credentials'] = True
            return response

        # 假设验证成功，创建 session 并返回成功消息
        request.session['user_id'] = user.user_id
        request.session['user_role'] = user.role
        print(request.session['user_role'])
        print(request.session['user_id'])
        response = JsonResponse({'message': 'Login successful'})
        response['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response['Access-Control-Allow-Credentials'] = True
        return response

    else:
        logger.error('Invalid request method')  # 打印错误信息
        response = JsonResponse({'error': 'Invalid request method'}, status=405)
        return response


# 检查用户是否登录
def check_session(request):
    if 'user_id' in request.session and 'user_role' in request.session:
        # 用户已登录，返回用户信息
        user_id = request.session['user_id']
        user_role = request.session['user_role']
        print(request.session['user_role']) 
        return JsonResponse({'user_id': user_id, 'user_role': user_role})
    else:
        # 用户未登录，返回401状态码
        return JsonResponse({'error': 'Not logged in'}, status=401)
    
# payment
@csrf_exempt
def payment(request, listid):
    if request.method == 'POST':
        data = json.loads(request.body)
        cardName = data.get('cardName')
        cardNumber = data.get('cardNumber')
        expMonth = data.get('expMonth')
        expYear = data.get('expYear')
        cvv = data.get('cvv')
        firstName = data.get('firstName')
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        zip = data.get('zip')
        email = data.get('email')
        amount = data.get('amount')
        user_id = data.get('userId')

        # fetch user from session
        user = User.objects.get(user_id=user_id)

        if not user:
            return JsonResponse({'error': 'User is not authenticated'}, status=401)
        

        

        # 处理支付逻辑
        return JsonResponse({'message': f'Payment of ${amount} completed successfully'})

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

#profile
@csrf_exempt
def profile(request):
    if request.method == 'PUT':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User is not authenticated'}, status=401)

        data = json.loads(request.body)
        user = request.user

        # 更新用户个人资料
        user.username = data.get('username', user.username)
        user.set_password(data.get('password', user.password))  # 更新密码
        user.save()

        # 更新其他个人资料字段
        user.profile.avatar = data.get('avatar', user.profile.avatar)
        user.profile.address = data.get('address', user.profile.address)
        user.profile.payment_method = data.get('payment_method', user.profile.payment_method)
        user.profile.save()

        return JsonResponse({'message': 'Profile updated successfully'})

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
#logout
def logout_view(request):
    logout(request)
    print('Logged out successfully')
    return JsonResponse({'message': 'Logout successful'})