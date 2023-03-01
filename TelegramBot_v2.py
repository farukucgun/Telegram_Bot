# find the cheapest product --> done, add it now
# spotify - youtube
# to do list and a reminder for it
# get news about a topic
# separate the commands that don't require user input and handle them using command handler

from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import requests
import geocoder
import datetime
import bs4
from time import sleep
from threading import Thread
from geopy.geocoders import Nominatim
import pyshorteners
import os
from dotenv import load_dotenv

load_dotenv()

telegram_auth_token = os.getenv('telegram_auth_token')
api_key = os.getenv('api_key')

updater = Updater(telegram_auth_token, use_context=True)


def get_weather(city):
    g = geocoder.ip('me')
    lat = g.lat
    lng = g.lng

    if city is not None:
        geolocator = Nominatim(user_agent="Your_Name")
        location = geolocator.geocode(city)
        lat = location.latitude
        lng = location.longitude

    hourly_params = "temperature_2m,windspeed_10m,rain"
    daily_params = "rain_sum,sunrise,sunset,temperature_2m_max,temperature_2m_min"

    res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}"
                       f"&timezone=auto&hourly={hourly_params}&daily={daily_params}")

    data = res.json()
    daily = data['daily']
    hourly = data['hourly']

    daily_rain = f"Rain for today: {daily['rain_sum'][0]} mm\n"
    daily_sunrise = f"Sunrise time for today: {str(daily['sunrise'][0]).split('T')[1]}\n"
    daily_sunset = f"Sunset time for today: {str(daily['sunset'][0]).split('T')[1]}\n"
    daily_max_temp = f"Maximum temperature for today: {daily['temperature_2m_max'][0]} °C\n"
    daily_min_temp = f"Minimum temperature for today: {daily['temperature_2m_min'][0]} °C\n"

    message = "--Daily Summary--\n\n" + daily_sunrise + daily_sunset + daily_rain + daily_max_temp + daily_min_temp + \
        "\n--Detailed Weather--\n\n"

    for i in range(24):
        message += f"{str(hourly['time'][i]).split('T')[1]}:   {hourly['temperature_2m'][i]} °C with wind speed:   " \
                   f"{hourly['windspeed_10m'][i]} km/h and {hourly['rain'][i]} mm rain\n"

    return message


def get_meal(dummy):
    day_of_week = datetime.date.today().weekday()
    res = requests.get("http://kafemud.bilkent.edu.tr/monu_eng.html")
    soup = bs4.BeautifulSoup(res.content, "lxml")

    meals = [[]]
    for i in range(0, 8):
        meals.insert(i, [5 * i + 4, 5 * i + 5, 5 * i + 6, 5 * i + 7])

    table = soup.find_all("table")[3]
    blocks = table.find_all("td")

    lunch = " ".join(blocks[meals[day_of_week][0]].getText().split())
    lunch_nutr = " ".join(blocks[meals[day_of_week][1]].getText().split())

    dinner = " ".join(blocks[meals[day_of_week][2]].getText().split())
    dinner_nutr = " ".join(blocks[meals[day_of_week][3]].getText().split())

    i = 0
    while i < len(dinner_nutr):
        if dinner_nutr[i] == '%':
            dinner_nutr = dinner_nutr[:i + 1] + " " + dinner_nutr[i + 1:]
            i += 1
        i += 1

    message = lunch.split('Lunch')[0] + "\n" + lunch.split('Lunch')[1] + "\n\nBesin değeri / Nutrition Facts\n" + \
        lunch_nutr + "\n\n" + dinner.split('Dinner')[0] + "\n" + dinner.split('Dinner')[1] + \
        "\n\nBesin değeri / Nutrition Facts\n" + dinner_nutr

    return message


def help(dummy):
    return "Here are some commands for you to get started:\n" \
           "/weather --> get daily weather forecast of Ankara\n" \
           "/weather city_name --> get daily weather forecast of city_name\n" \
           "/meal --> get the daily meal schedule for Bilkent\n" \
           "/urlshortener url --> shorten the url passed\n" \
           "/timer min --> set a timer and get a message after min minutes\n" \
           "/reminder note month-day-hour-minute --> set a reminder for the date entered\n"


def url_shortener(url):
    type_bitly = pyshorteners.Shortener(api_key=api_key)
    short_url = type_bitly.bitly.short(url)
    return short_url


def timer(total):
    while total > 0:
        sleep(1)
        total -= 1


def countdown(minutes=1):
    total = int(minutes) * 60
    timer_thread = Thread(target=timer(total))
    timer_thread.start()
    if not timer_thread.is_alive():
        return "time is up!"


def reminder(text, date_input):
    d = datetime.datetime.now()
    date = date_input.split("-")
    if date[0] == str(d.month) and date[1] == str(d.day) and date[2] == str(d.hour) and date[3] == str(d.minute):
        return text
    return ""


def test_api(dummy):
    res = requests.get('http://localhost:5000/meal')
    data = res.json()
    return data["today's meal"]


def take_input(update: Update, context: CallbackContext):
    is_command = update.message.text[0] == "/"
    command = update.message.text[1:]
    user_input = None

    if " " in update.message.text:
        command = update.message.text.split(" ")[0][1:]
        user_input = update.message.text.split(" ")[1]

    if command == "meal":
        update.message.reply_text(get_meal(user_input))

    elif command == "weather":
        update.message.reply_text(get_weather(user_input))

    elif command == "help":
        update.message.reply_text(help(user_input))

    elif command == "urlshortener":
        update.message.reply_text(url_shortener(user_input))

    elif command == "timer":
        update.message.reply_text(countdown(user_input))

    elif command  == "reminder":
        user_input2 = update.message.text.split(" ")[2]
        update.message.reply_text(reminder(user_input, user_input2))

    elif is_command:
        update.message.reply_text("Sorry, I am unable to understand you. " + help(user_input))


def unknown_text(update: Update, context: CallbackContext):  # reply to the unknown text messages
    update.message.reply_text(
        "Sorry I can't recognize you , you said '%s'" % update.message.text)


def unknown(update: Update, context: CallbackContext):  # reply to the unknown commands
    update.message.reply_text(f"Sorry '{update.message.text}' is not a valid command\n"
                              f"Type /help to see the available commands")


updater.dispatcher.add_handler(MessageHandler(Filters.text, take_input)) # handles commands and inputs
# updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))  # Filters out unknown commands
# updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))  # Filters out unknown messages

updater.start_polling()
