import json
import os
import dotenv
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from dotenv import load_dotenv
load_dotenv()


# Create your views here.


def server_start(request):
    return HttpResponse("Server started successfully. \n Make sure to double"
                        "check environment variables for allowed hosts.")


def admin_reports(request):
    class Car:
        def __init__(self, listid, make, image, model, color, year,
                     reason_for_report, seller, reporter):
            self.make = make
            self.listid = listid
            self.image = image
            self.model = model
            self.color = color
            self.year = year
            self.reason_for_report = reason_for_report
            self.seller = seller
            self.reporter = reporter

        def serialize(self):
            return {
                "listid": self.listid,
                "make": self.make,
                "image": self.image,
                "model": self.model,
                "color": self.color,
                "year": self.year,
                "reason_for_report": self.reason_for_report,
                "seller": self.seller,
                "reporter": self.reporter
            }

    car = Car(12345, "Tesla", "data:image/jpeg;base64,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",
              "Model 3", "White", 2023, "Something wrong with the car",
              "Seller A", "Reporter A")
    car2 = Car(12346, "Toyota", "data:image/jpeg;base64,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",
               "Prius", "Blue", 2017, "Something really wrong with this car",
               "Seller A", "Reporter B")

    cars = [car, car2, car, car2, car, car2, car, car2]

    if cars:
        cars_json = json.dumps([car.serialize() for car in cars])
        return HttpResponse(cars_json)
    else:
        return HttpResponse(status=404)


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
