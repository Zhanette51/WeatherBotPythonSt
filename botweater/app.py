import os 
import requests
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from dotenv import load_dotenv

load_dotenv()


def get_weather():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session) 
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 53.2001,
        "longitude": 50.15,
        "hourly": "temperature_2m",
        "forecast_days": 1,
    }
    responses = openmeteo.weather_api(url, params=params)
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
    
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    
    hourly_data["temperature_2m"] = hourly_temperature_2m
    
    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print("\nHourly data\n", hourly_dataframe)
    return hourly_dataframe.to_markdown(index=None)

def send_message(message):

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

    url=f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    params= {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': f'```\n{message}```'
    }

    res = requests.get(url, params=params)
    return res.json()

if __name__ == '__main__':
    weather = get_weather()
    result = send_message(weather)  # Сохраняем результат
    print("Результат отправки:", result)  