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
    return HttpResponse(
        "Server started successfully. \n Make sure to double"
        "check environment variables for allowed hosts."
    )


def admin_reports(request):
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
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
        """
        )
        rows = cursor.fetchall()

        data = [
            {
                "ListId": row[0],
                "Image": row[1],
                "Make": row[2],
                "Model": row[3],
                "Seller": row[4],
                "SellerId": row[5],
                "Description": row[6],
                "Reporter": row[7],
                "ReporterId": row[8],
            }
            for row in rows
        ]
        return JsonResponse(data, safe=False)

    except Exception as e:
        return HttpResponse(str(e), status=404)


def all_listings(request):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 
            cl.listid, cl.licenseNumber, cl.engineSerialNumber, cl.make, cl.model, 
            cl.year, cl.mileage, cl.city, cl.color, cl.additionalFeatures, 
            cl.description, cl.startingPrice, cl.biddingDeadline, cl.highestBid, 
            cl.highestBidHolder, u.username, cl.image
        FROM 
            CarListing cl
            JOIN User u ON cl.sellerID = u.user_id
    """
    )


def all_listings(request):
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 
            cl.listid, cl.licenseNumber, cl.engineSerialNumber, cl.make, cl.model, 
            cl.year, cl.mileage, cl.city, cl.color, cl.additionalFeatures, 
            cl.description, cl.startingPrice, cl.biddingDeadline, cl.highestBid, 
            cl.highestBidHolder, u.username, cl.image
        FROM 
            CarListing cl
            JOIN User u ON cl.sellerID = u.user_id
    """
    )

    rows = cursor.fetchall()

    data = [
        {
            "listid": row[0],
            "licenseNumber": row[1],
            "engineSerialNumber": row[2],
            "make": row[3],
            "model": row[4],
            "year": row[5],
            "mileage": row[6],
            "city": row[7],
            "color": row[8],
            "additionalFeatures": row[9],
            "description": row[10],
            "startingPrice": row[11],
            "biddingDeadline": row[12],
            "highestBid": row[13],
            "highestBidHolder": row[14],
            "sellerUsername": row[15],
            "image": row[16],
        }
        for row in rows
    ]

    return JsonResponse(data, safe=False)


def website_stats(request):
    try:
        cursor = connection.cursor()
        cursor.execute('''SELECT 
            COUNT(*) as Total_Sales, 
             date
        FROM Transactions
        GROUP BY 
            date;''')
        rows = cursor.fetchall()
        cursor.execute('''
            SELECT COUNT(model)as model_sales, model
            FROM
            (SELECT 
                COUNT(*) as Total_Sales, 
                model, date
            FROM (
                SELECT * 
                FROM Transactions t
                INNER JOIN CarListing c ON t.list_id = c.listid
            ) as joint
            GROUP BY 
                date, 
                model) as sub
                GROUP BY model
            ORDER BY model_sales DESC;
        ''')
        rows2 = cursor.fetchall()
        sales = [
            {
                "Total_Sales": row[0],
                "Date":row[1]
            }
            for row in rows
        ]
        model_sales = [
            {
                "Sold": row[0],
                "Model": row[1]
            }
            for row in rows2
        ]
        data = {
            "sales": sales,
            "model_sales": model_sales
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse(str(e), status=404)



def detail_page(request, listid):
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
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
        """,
            [listid],
        )

        row = cursor.fetchone()

        if row:
            car_data = {
                "listid": row[0],
                "licenseNumber": row[1],
                "engineSerialNumber": row[2],
                "make": row[3],
                "model": row[4],
                "year": row[5],
                "mileage": row[6],
                "city": row[7],
                "color": row[8],
                "additionalFeatures": row[9],
                "description": row[10],
                "startingPrice": row[11],
                "biddingDeadline": row[12],
                "highestBid": row[13],
                "highestBidHolder": row[14],
                "sellerUsername": row[15],
                "highestBidHolderUsername": (
                    row[16] if row[16] else "No highest bid holder"
                ),
                "image": row[17],
            }

            return JsonResponse(car_data)
        else:
            return HttpResponse(status=404)
    finally:
        cursor.close()


@csrf_exempt
def post_listing(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            values = (
                data.get("sellerID", 1),  # Default value set to 1
                data.get("licenseNumber", ""),
                data.get("engineSerialNumber", ""),
                data.get("make", ""),
                data.get("model", ""),
                data.get("year", 0),
                data.get("mileage", 0),
                data.get("city", ""),
                data.get("color", ""),
                data.get("additionalFeatures", ""),
                data.get("description", ""),
                data.get("startingPrice", 0),
                data.get("biddingDeadline", ""),
                -1,  # Assuming -1 is the default value for highestBid and highestBidHolder
                1,  # Assuming 1 is the default value for highestBidHolder
                data.get("image", ""),
            )

            # Execute the SQL query.
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO CarListing
                    (sellerID, licenseNumber, engineSerialNumber, make, model, year, mileage, city, color, additionalFeatures, description, startingPrice, biddingDeadline, highestBid, highestBidHolder, image)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, STR_TO_DATE(%s, '%%Y-%%m-%%dT%%H:%%i:%%sZ'), %s, %s, %s)
                """,
                    values,
                )

            return JsonResponse(
                {"status": "success", "message": "Listing created successfully"}
            )

        except Exception as e:
            # Handle other exceptions
            return JsonResponse(
                {"status": "error", "message": "An error occurred: " + str(e)}
            )
    else:
        # If the method is not POST, return an error
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"}, status=405
        )


@csrf_exempt
def submit_bid(request):
    if not request.method == "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid request method"}, status=405
        )

    if not request.session.get("user_id"):
        return JsonResponse(
            {"success": False, "message": "User not logged in"}, status=401
        )

    try:
        data = json.loads(request.body)
        bid = float(data.get("bid"))
        listing_id = data.get("listing_id")
        user_id = request.session.get("user_id")

        with connection.cursor() as cursor:
            # Fetch the current highest bid
            cursor.execute(
                "SELECT highestBid FROM CarListing WHERE listid = %s", [listing_id]
            )
            row = cursor.fetchone()
            if row:
                current_highest_bid = row[0]
                if bid > current_highest_bid:
                    # Update the bid
                    cursor.execute(
                        "UPDATE CarListing SET highestBid = %s, highestBidHolder = %s WHERE listid = %s",
                        [bid, user_id, listing_id],
                    )
                    # Fetch the username of the highest bid holder
                    cursor.execute(
                        "SELECT username FROM user WHERE user_id = %s", [user_id]
                    )
                    user_row = cursor.fetchone()
                    if user_row:
                        highest_bid_holder_username = user_row[0]
                        return JsonResponse(
                            {
                                "success": True,
                                "message": "Bid placed successfully",
                                "highestBidHolderUsername": highest_bid_holder_username,  # include the username in the response
                            }
                        )
                    else:
                        return JsonResponse(
                            {"success": False, "message": "User not found"}, status=404
                        )
            else:
                return JsonResponse(
                    {"success": False, "message": "Car listing not found"}, status=404
                )

    except KeyError:
        return JsonResponse(
            {"success": False, "message": "Missing required data"}, status=400
        )
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Invalid bid value"}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"An unexpected error occurred: {e}"},
            status=500,
        )


@csrf_exempt
def post_report(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    if request.method == "POST":
        if not request.session.get("user_id"):
            return JsonResponse({"error": "User not logged in"}, status=401)

        try:
            data = json.loads(request.body)
            reporter_id = request.session.get("user_id")
            description = data["description"]
            listing_id = int(data["listing_id"])
            submit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # submit_time = datetime.now()

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ListingReport (reporter_id, submit_time, description, listing_id) 
                    VALUES (%s, %s, %s, %s)
                """,
                    [reporter_id, submit_time, description, listing_id],
                )

            return JsonResponse({"message": "Report submitted successfully"})

        except KeyError as e:
            return HttpResponseBadRequest(f"Missing field: {e}")
        except ValueError as e:
            # This will catch issues like conversion errors
            return HttpResponseBadRequest(f"Invalid data: {e}")
        except DatabaseError as e:
            # Specific handling for database errors
            return HttpResponseBadRequest(f"Database error: {e}")
        except Exception as e:
            # Catch-all for any other exceptions
            return HttpResponseBadRequest(f"An unexpected error occurred: {e}")


# 用户注册
@csrf_exempt  # 禁用 CSRF 防护，以便前端可以发送 POST 请求
def signup(request):
    if request.method == "POST":
        # 从前端拿用户名和密码
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        # 检查一下用户名是否已经存在
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        # 创建一个user然后存到数据库user表里
        user = User.objects.create(username=username, password=password, role="normal")

        # 注册成功
        response = JsonResponse({"message": "User created successfully"})
        response["Access-Control-Allow-Origin"] = (
            "http://localhost:3000"  # 允许跨域请求
        )
        response["Access-Control-Allow-Credentials"] = True  # 允许携带凭据
    else:
        # 如果不是 POST 请求，返回错误消息
        response = JsonResponse({"error": "Invalid request method"}, status=405)

    return response


# 登录
@csrf_exempt
def login(request):
    logger.debug("Login request received")  # 打印调试信息

    if request.method == "OPTIONS":
        logger.debug("Handling preflight request")  # 打印调试信息
        response = JsonResponse({"message": "Preflight request handled successfully"})
        response["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response["Access-Control-Allow-Credentials"] = True
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST"
        return response

    elif request.method == "POST":
        logger.debug("Handling POST request")  # 打印调试信息
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("User does not exist")  # 打印错误信息
            response = JsonResponse({"error": "Username does not exist"}, status=401)
            response["Access-Control-Allow-Origin"] = "http://localhost:3000"
            response["Access-Control-Allow-Credentials"] = True
            return response

        print("输入的密码:", password)
        print("数据库中存储的密码:", user.password)

        # 验证密码是否匹配
        if password != user.password:
            logger.error("Invalid password")  # 打印错误信息
            response = JsonResponse({"error": "Invalid password"}, status=401)
            response["Access-Control-Allow-Origin"] = "http://localhost:3000"
            response["Access-Control-Allow-Credentials"] = True
            return response

        # 假设验证成功，创建 session 并返回成功消息
        request.session["user_id"] = user.user_id
        request.session["user_role"] = user.role
        print(request.session["user_role"])
        print(request.session["user_id"])
        response = JsonResponse({"message": "Login successful"})
        response["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response["Access-Control-Allow-Credentials"] = True
        return response

    else:
        logger.error("Invalid request method")  # 打印错误信息
        response = JsonResponse({"error": "Invalid request method"}, status=405)
        return response


# 检查用户是否登录


def check_session(request):
    if "user_id" in request.session and "user_role" in request.session:
        # 用户已登录，返回用户信息
        user_id = request.session["user_id"]
        user_role = request.session["user_role"]
        print(request.session["user_role"])
        return JsonResponse({"user_id": user_id, "user_role": user_role})
    else:
        # 用户未登录，返回401状态码
        return JsonResponse({"error": "Not logged in"}, status=401)


# payment
@csrf_exempt
def payment(request, listid):
    if request.method == "POST":
        data = json.loads(request.body)
        cardName = data.get("cardName")
        cardNumber = data.get("cardNumber")
        expMonth = data.get("expMonth")
        expYear = data.get("expYear")
        cvv = data.get("cvv")
        firstName = data.get("firstName")
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        zip = data.get("zip")
        email = data.get("email")
        amount = data.get("amount")
        user_id = data.get("userId")

        # fetch user from session
        user = User.objects.get(user_id=user_id)

        if not user:
            return JsonResponse({"error": "User is not authenticated"}, status=401)

        # 处理支付逻辑
        return JsonResponse({"message": f"Payment of ${amount} completed successfully"})

    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


# payment
@csrf_exempt
def payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        listid = data.get("listid")
        user_id = data.get("userId")
        amount = data.get("amount")
        cardName = data.get("cardName")
        cardNumber = data.get("cardNumber")
        expMonth = data.get("expMonth")
        expYear = data.get("expYear")
        cvv = data.get("cvv")
        firstName = data.get("firstName")
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        zip = data.get("zip")
        email = data.get("email")

        # fetch user from session
        user = User.objects.get(user_id=user_id)

        if not user:
            return JsonResponse({"error": "User is not authenticated"}, status=401)

        cursor = connection.cursor()
        cursor.execute(
            f"""
            INSERT INTO Transactions (listid, cardName, cardNumber, expMonth, expYear, cvv, firstName, address, city, state, zip, email, amount, user_id)
            VALUES ({listid}, '{cardName}', '{cardNumber}', '{expMonth}', '{expYear}', '{cvv}', '{firstName}', '{address}', '{city}', '{state}', '{zip}', '{email}', {amount}, {user_id})
        """
        )
        return JsonResponse({"message": "Payment successful"}, 200)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def check_table(request, tablename):
    cursor = connection.cursor()
    cursor.execute(f"DESCRIBE {tablename}")
    rows = cursor.fetchall()
    return JsonResponse(rows, safe=False)


def fecth_table_data(request, tablename):
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {tablename}")
    rows = cursor.fetchall()
    return JsonResponse(rows, safe=False)


def add_fake_data(request):
    # add fake data to the Transactions table
    cursor = connection.cursor()

    cursor.execute(
        """
            INSERT INTO Payment (user_id, cardName, cardNumber, expMonth, expYear, cvv) 
            VALUES (1, 'John Doe', '123456789', '12', '2023', '123'),
                    (2, 'Jane Bob', '987654321', '11', '2022', '456'),
                    (3, 'John Doe', '123456789', '12', '2023', '123'),
                    (4, 'Jane Bob', '987654321', '11', '2022', '456'),
                    (5, 'John Doe', '123456789', '12', '2023', '123')
        """,
    )

    cursor.execute(
        """
            INSERT INTO Address (user_id, fullName, address, city, state, zip, email) 
            VALUES  (1, "user1", '123 Main St', 'New York', 'NY', '10001', 'john.doe@gmail.com'),
                    (2, "user2", '456 Elm St', 'Los Angeles', 'CA', '90001', 'john.bob@gmail.com'),
                    (3, "user3", '123 Main St', 'New York', 'NY', '10001', 'user3@gmail.com'),
                    (4, "user4", '456 Elm St', 'Los Angeles', 'CA', '90001', 'user4@gmail.com'),
                    (5, "user5", '123 Main St', 'New York', 'NY', '10001', 'user4@gmail.com')
        """,
    )

    cursor.execute(
        """
        INSERT INTO Transactions (owner_id, buyer_id, list_id, amount, data, payment_id, address_id)
        VALUES  (1, 3, 1, 5000.00, '2021-03-01',  3, 3),
                (1, 4, 1, 8000.00, '2021-03-02',  4, 4),
                (1, 5, 1, 10000.00, '2021-03-03', 5, 5),
                (2, 3, 2, 12000.00, '2021-03-04', 3, 3),
                (2, 4, 2, 15000.00, '2021-03-05', 4, 4),
                (2, 5, 2, 16000.00, '2021-03-06', 5, 5)
    """
    )
    return JsonResponse({"message": "Fake data added successfully"}, status=200)


def create_transaction_tables(request):
    cursor = connection.cursor()
    # # start a transaction
    # cursor.execute("START TRANSACTION")
    cursor.execute("DROP TABLE IF EXISTS Transactions")
    cursor.execute("DROP TABLE IF EXISTS Payment")
    cursor.execute("DROP TABLE IF EXISTS Shipping")
    cursor.execute("DROP TABLE IF EXISTS Address")

    cursor.execute(
        """
        CREATE TABLE Payment (
            payment_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            cardName VARCHAR(255) NOT NULL,
            cardNumber VARCHAR(255) NOT NULL,
            expMonth VARCHAR(255) NOT NULL,
            expYear VARCHAR(255) NOT NULL,
            cvv VARCHAR(255) NOT NULL,

            FOREIGN KEY (user_id) REFERENCES user(user_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE Address (
            address_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT,
            fullName VARCHAR(255) NOT NULL,
            address VARCHAR(255) NOT NULL,
            city VARCHAR(255) NOT NULL,
            state VARCHAR(255) NOT NULL,
            zip VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,

            FOREIGN KEY (user_id) REFERENCES user(user_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE Transactions (
            transaction_id INT PRIMARY KEY AUTO_INCREMENT,
            owner_id INT,
            buyer_id INT,
            list_id INT,
            amount FLOAT NOT NULL,
            data DATE NOT NULL,
            payment_id INT,
            address_id INT,

            FOREIGN KEY (owner_id) REFERENCES user(user_id),
            FOREIGN KEY (buyer_id) REFERENCES user(user_id),
            FOREIGN KEY (list_id) REFERENCES CarListing(listid),
            FOREIGN KEY (payment_id) REFERENCES Payment(payment_id),
            FOREIGN KEY (address_id) REFERENCES Address(address_id)
        )
    """
    )

    # fecth description of all Transactions table
    cursor.execute("DESCRIBE Transactions")
    rows = cursor.fetchall()

    return JsonResponse(rows, safe=False)


# fetch all transactions
@csrf_exempt
def fetch_transactions(request):
    if request.method == "GET":
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.transaction_id, t.cardName, t.cardNumber, t.expMonth, t.expYear, t.cvv, t.firstName, t.address, t.city, t.state, t.zip, t.email, t.amount, t.user_id
            FROM Transaction t
        """
        )

        rows = cursor.fetchall()
        data = [
            {
                "transaction_id": row[0],
                "cardName": row[1],
                "cardNumber": row[2],
                "expMonth": row[3],
                "expYear": row[4],
                "cvv": row[5],
                "firstName": row[6],
                "address": row[7],
                "city": row[8],
                "state": row[9],
                "zip": row[10],
                "email": row[11],
                "amount": row[12],
                "user_id": row[13],
            }
            for row in rows
        ]

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


# profile
@csrf_exempt
def profile(request):
    if request.method == "PUT":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "User is not authenticated"}, status=401)

        data = json.loads(request.body)
        user = request.user

        # 更新用户个人资料
        user.username = data.get("username", user.username)
        user.set_password(data.get("password", user.password))  # 更新密码
        user.save()

        # 更新其他个人资料字段
        user.profile.avatar = data.get("avatar", user.profile.avatar)
        user.profile.address = data.get("address", user.profile.address)
        user.profile.payment_method = data.get(
            "payment_method", user.profile.payment_method
        )
        user.profile.save()

        return JsonResponse({"message": "Profile updated successfully"})

    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


# logout
def logout_view(request):
    logout(request)
    print("Logged out successfully")
    return JsonResponse({"message": "Logout successful"})
