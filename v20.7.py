from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import requests
import datetime
import os
from dotenv import load_dotenv
import geocoder
from geopy.geocoders import Nominatim
import bs4
import pyshorteners
import asyncio
from googletrans import Translator, constants
from functools import wraps
import re

####################
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

news_countries = ["ae","ar","at","au","be","bg","br","ca","ch","cn","co","cu","cz","de","eg","fr","gb","gr","hk","hu","id","ie",
                    "il","in","it","jp","kr","lt","lv","ma","mx","my","ng","nl","no","nz","ph","pl","pt","ro","rs","ru","sa","se",
                    "sg","si","sk","th","tr","tw","ua","us","ve","za"]

news_categories = ["business","entertainment","general","health","science","sports","technology"]
####################

"""
not allowed groups and users can only use /request and it sends me a message of their request to use the bot
admin only functionalities, respond to specific users only
check filter types and act accordingly (photos etc)
upload data to a specific folder in cloud
calender events or tasks in the morning (connect to task management apps, reminder for them?)
get the weather forecast for a specific day
find the cheapest product
currency exchange rates
take anonymous feedback
trivia quiz and word game
create polls, surveys
respond to normal messages (enable from botfather)
login to srs --> get the cookies 
"""


def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes):
        # user_id = update.effective_user.id
        # if str(user_id) not in os.getenv('allowed_users'):
        #     logger.info("Unauthorized access denied for {}.".format(update.effective_user.id))
        #     return
        
        group_id = update.effective_chat.id
        if str(group_id) not in os.getenv('allowed_groups'):
            logger.info("Unauthorized access denied for {}.".format(group_id))
            return
        return await func(update, context)
    return wrapped


@restricted
async def help(update: Update, context: ContextTypes):
    if len(update.message.text.split(' ')) > 1:
        command = update.message.text.split(' ')[1]
        if command == "help":
            await update.message.reply_text("Usage: /help \n\n" + "This will show the available commands")
        elif command == "weather":
            await update.message.reply_text("Usage: /weather [request_type] [city] \n\n" + "Supported Request Types: current, hourly, daily \n\n" + "Example: /weather current Ankara \n\n" + "This will show the current weather for Ankara. If no request type is given, current weather will be shown. If no city is given, Ankara's weather will be shown.")
        elif command == "menu":
            await update.message.reply_text("Usage: /menu [day] \n\n" + "Supported Days: 1-7 \n\n" + "Example: /menu 1 \n\n" + "This will show the menu for Monday. If no day is given, today's menu will be shown.")
        elif command == "shorten":
            await update.message.reply_text("Usage: /shorten <url> \n\n" + "Example: /shorten https://www.google.com \n\n" + "This will shorten the url")
        elif command == "timer":
            await update.message.reply_text("Usage: /timer <time in minutes> \n\n" + "Example: /timer 5 \n\n" + "This will start a timer for 5 minutes")
        elif command == "translate":
            await update.message.reply_text("Usage: /translate \"<text>\" <destination language> \n\n" + "Supported Languages: " + str(constants.LANGUAGES) + "\n\n" + "Example: /translate \"Hello World\" tr \n\n" + "This will translate the text to Turkish")
        elif command == "news":
            await update.message.reply_text("Usage: /news <country> <category> <query> \n\n" + "Supported Countries: " + str(news_countries) + "\n" + "Supported Categories: " + str(news_categories) + "\n\n" + "Use a dot(.) for empty parameters \n\n" + "Example: /news tr general . \n\n" + "This will show the top 5 news for Turkey in general category")
        else:
            await update.message.reply_text("Invalid command \n\n" + "Available commands: \n\n" + "/help - Shows this message \n\n" + "/weather - Shows the weather for the given city \n\n" + "/menu - Shows the menu for the given day \n\n" + "/shorten - Shortens the given url \n\n" + "/timer - Starts a timer for the given time \n\n" + "/translate - Translates the given text to the given language \n\n" + "/news - Shows the top 5 news for the given country, category and query \n\n" + "For more information about a command, type /help <command>")
    else:
        await update.message.reply_text("Available commands: \n\n" + "/help - Shows this message \n\n" + "/weather - Shows the weather for the given city \n\n" + "/menu - Shows the menu for the given day \n\n" + "/shorten - Shortens the given url \n\n" + "/timer - Starts a timer for the given time \n\n" + "/translate - Translates the given text to the given language \n\n" + "/news - Shows the top 5 news for the given country, category and query \n\n" + "For more information about a command, type /help <command>")


@restricted
async def echo(update: Update, context: ContextTypes):
    await update.message.reply_text(update.message.text)


@restricted
async def get_weather(update: Update, context: ContextTypes):
    help = "Usage: /weather [request_type] [city] \n\n" + "Supported Request Types: current, hourly, daily \n\n" + "Example: /weather current Ankara \n\n" + "This will show the current weather for Ankara. If no request type is given, current weather will be shown. If no city is given, Ankara's weather will be shown."
    params = update.message.text.split(' ')[1:] if len(update.message.text.split(' ')) > 1 else None
    city = "Ankara"
    request_type = "current"
    if params is not None:
        if params[0] in ["current", "hourly", "daily"]:
            request_type = params[0]
            city = params[1] if len(params) > 1 else "Ankara"
        else:
            city = params[0]

    geolocator = Nominatim(user_agent="Your_Name")
    location = geolocator.geocode(city)
    if location is None:
        await update.message.reply_text("Invalid city \n\n" + help)
        return
    
    lat = location.latitude
    lng = location.longitude

    if request_type == "current":
        weather_params = "current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,showers,snowfall,wind_speed_10m"
    elif request_type == "hourly":
        weather_params = "hourly=temperature_2m,precipitation_probability,precipitation,wind_speed_10m"
    elif request_type == "daily":
        weather_params = "daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max"
    else:
        await update.message.reply_text("Invalid request type \n\n" + help)
        return

    forecast_days = 1
    res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&timezone=auto&{weather_params}&forecast_days={forecast_days}")

    data = res.json()

    if request_type == "current":
        current = data['current']
        current_units = data['current_units']
        message = f"Current weather for {city}: \n\n" \
                  f"Temperature: {current['temperature_2m']} {current_units['temperature_2m']}\n" \
                  f"Apparent Temperature: {current['apparent_temperature']} {current_units['apparent_temperature']}\n" \
                  f"Relative Humidity: {current['relative_humidity_2m']} {current_units['relative_humidity_2m']}\n" \
                  f"Precipitation: {current['precipitation']} {current_units['precipitation']}\n" \
                  f"Rain: {current['rain']} {current_units['rain']}\n" \
                  f"Showers: {current['showers']} {current_units['showers']}\n" \
                  f"Snowfall: {current['snowfall']} {current_units['snowfall']}\n" \
                  f"Wind Speed: {current['wind_speed_10m']} {current_units['wind_speed_10m']}\n"
        
        await update.message.reply_text(message)
        return

    elif request_type == "hourly":
        hourly = data["hourly"]
        hourly_units = data["hourly_units"]
        message = f"Hourly weather for {city}: \n\n"
        for i in range(24):
            message += f"{str(hourly['time'][i]).split('T')[1]}: {hourly['temperature_2m'][i]} {hourly_units['temperature_2m']} " \
                       f"and {hourly['precipitation'][i]} {hourly_units['precipitation']} rain " \
                       f"with probability: {hourly['precipitation_probability'][i]} {hourly_units['precipitation_probability']} " \
                       f"and wind speed: {hourly['wind_speed_10m'][i]} {hourly_units['wind_speed_10m']} \n\n"
                    
        await update.message.reply_text(message)
        return
    
    elif request_type == "daily":
        daily = data["daily"]
        daily_units = data["daily_units"]
        message = f"Daily weather for {city}: \n\n" \
                  f"Sunrise: {str(daily['sunrise'][0]).split('T')[1]}\n" \
                  f"Sunset: {str(daily['sunset'][0]).split('T')[1]}\n" \
                  f"Rain: {daily['precipitation_sum'][0]} {daily_units['precipitation_sum']}\n" \
                  f"Rain Probability: {daily['precipitation_probability_max'][0]} {daily_units['precipitation_probability_max']}\n" \
                  f"Maximum Temperature: {daily['temperature_2m_max'][0]} {daily_units['temperature_2m_max']}\n" \
                  f"Minimum Temperature: {daily['temperature_2m_min'][0]} {daily_units['temperature_2m_min']}\n"
        
        await update.message.reply_text(message)
        return

    else :
        await update.message.reply_text("Invalid request type \n\n" + help)
        return


@restricted
async def menu(update: Update, context: ContextTypes):
    help = "Usage: /menu [day] \n\n" + "Supported Days: 1-7 \n\n" + "Example: /menu 1 \n\n" + "This will show the menu for Monday. If no day is given, today's menu will be shown."
    day = update.message.text.split(' ')[1] if len(update.message.text.split(' ')) > 1 else None
    day_of_week = datetime.date.today().weekday()

    if day is not None:
        try: 
            day = int(day)
        except ValueError:
            await update.message.reply_text("Day should be an integer value \n\n" + help)
            return
        
        if day < 1 or day > 7:
            await update.message.reply_text("Invalid day \n\n" + help)
            return
        day_of_week = day - 1

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

    await update.message.reply_text(message)


@restricted
async def url_shortener(update: Update, context: ContextTypes):
    help = "Usage: /shorten <url> \n\n" + "Example: /shorten https://www.google.com \n\n" + "This will shorten the url"
    url = update.message.text.split(' ')[1] if len(update.message.text.split(' ')) > 1 else None
    if url is None:
        await update.message.reply_text("Please enter a url \n\n" + help)
        return
    
    type_bitly = pyshorteners.Shortener(api_key=os.getenv('api_key'))
    short_url = type_bitly.bitly.short(url)
    if short_url is None:
        await update.message.reply_text("Invalid url \n\n" + help)
        return
    
    await update.message.reply_text(short_url)


@restricted
async def timer(update: Update, context: ContextTypes):
    help = "Usage: /timer <time in minutes> \n\n" + "Example: /timer 5 \n\n" + "This will start a timer for 5 minutes"
    minutes = update.message.text.split(' ')[1] if len(update.message.text.split(' ')) > 1 else None
    if minutes is None:
        await update.message.reply_text("Please enter a time \n\n" + help)
        return
    
    try:
        minutes = int(minutes)
    except ValueError:
        await update.message.reply_text("Invalid time \n\n" + help)
        return 
    
    asyncio.create_task(timer_task(update, minutes))


@restricted
async def timer_task(update: Update, minutes: int):
    await update.message.reply_text("Timer started")
    await asyncio.sleep(minutes * 60)
    await update.message.reply_text("Timer ended")


@restricted
async def translate(update: Update, context: ContextTypes):
    help = "Usage: /translate \"<text>\" [source language] <destination language> \n\n" + "Supported Languages: " + str(constants.LANGUAGES) + "\n\n" + "Example: /translate \"Hello World\" en tr \n\n" + "This will translate the English text to Turkish \n\n" + "If no source language is given, it will be automatically detected"
    pattern = r'/translate(?:\s+"([^"]*)")?(?:\s+(\w+))?(?:\s+(\w+))?$'
    match = re.match(pattern, update.message.text)
    
    if match is None:
        await update.message.reply_text("Please enter a valid command \n\n" + help)
        return
    
    groups = match.groups()
    text = groups[0]
    
    if text is None:
        await update.message.reply_text("Please enter a text to translate \n\n" + help)
        return
    
    if groups[1] is not None and groups[2] is None:
        src_lang = "auto"
        dest_lang = groups[1]
    elif groups[1] is not None and groups[2] is not None:
        src_lang = groups[1]
        dest_lang = groups[2]
    else:
        src_lang = "auto"
        dest_lang = "en"
    
    if dest_lang not in constants.LANGUAGES:
        await update.message.reply_text("Invalid destination language \n\n" + help)
        return
    
    if src_lang not in constants.LANGUAGES and src_lang != "auto":
        await update.message.reply_text("Invalid source language \n\n" + help)
        return
    
    translator = Translator()
    translation = translator.translate(text, src=src_lang, dest=dest_lang)
    await update.message.reply_text(translation.text)    


@restricted
async def news(update: Update, context: ContextTypes):
    help = "Usage: /news <country> <category> <query> \n\n" + "Supported Countries: " + str(news_countries) + "\n" + "Supported Categories: " + str(news_categories) + "\n\n" + "Use a dot(.) for empty parameters \n\n" + "Example: /news tr general . \n\n" + "This will show the top 5 news for Turkey in general category"
    inputs = update.message.text.split(' ')[1:]
    if len(inputs) != 3:
        await update.message.reply_text("Please enter a valid command \n\n" + help)
        return
    
    country = inputs[0] if inputs[0] != "." else "tr"
    if country not in news_countries:
        await update.message.reply_text("Invalid country \n\n" + help)
        return 
    country_addition = "&country=" + country if country is not None else ""

    category = inputs[1] if inputs[1] != "." else "general"
    if category not in news_categories:
        await update.message.reply_text("Invalid category \n\n" + help)
        return
    category_addition = "&category=" + category if category is not None else ""

    query = inputs[2] if inputs[2] != "." else None
    query_addition = "&q=" + query if query is not None else ""
    
    res = requests.get("https://newsapi.org/v2/top-headlines?apiKey=" + str(os.getenv('news_api_key')) + country_addition + category_addition + query_addition)
    data = res.json()
    articles = data['articles']
    total_results = data['totalResults']

    if total_results == 0:
        await update.message.reply_text("No results found for the selected country, category and query \n\n" + help)
        return
        
    message = ""
    for i in range(0, 5):
        message += articles[i]['title'] + "\n" + articles[i]['url'] + "\n\n"
    await update.message.reply_text(message)
    

@restricted
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command. \n\n type /help for more information.")


def main():
    load_dotenv()
    telegram_auth_token = os.getenv('telegram_auth_token')
    application = Application.builder().token(telegram_auth_token).build()

    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("weather", get_weather))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("shorten", url_shortener))
    application.add_handler(CommandHandler("timer", timer))
    application.add_handler(CommandHandler("translate", translate))
    application.add_handler(CommandHandler("news", news))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()