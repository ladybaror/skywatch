import pika
import os
import json
import requests
import time

# משיכת ה-Host (אם רץ לוקאלית ישתמש ב-localhost, אם בקלאסטר ישתמש במה שמוגדר ב-YAML)
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")

def fetch_weather(city_name):
    """Directly queries Open-Meteo APIs for geocoding and weather data."""
    try:
        # 1. Convert City Name -> Latitude/Longitude using Open-Meteo Geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city_name, "count": 1}, timeout=5)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            print(f"[-] City '{city_name}' not found.", flush=True)  # <-- הוסף flush
            return

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        country = location.get("country", "Unknown")

        # 2. Fetch current weather using Latitude & Longitude
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=5)
        weather_data = weather_resp.json()

        current = weather_data.get("current_weather", {})

        # תיקון: הוספת flush=True לתוצאות האמיתיות
        print(f"[x] Successfully processed weather for {location['name']}, {country}:", flush=True)
        print(f"    Temperature: {current.get('temperature')}°C, Wind: {current.get('windspeed')} km/h", flush=True)
        
    except Exception as e:
        print(f"[!] Error processing weather for {city_name}: {str(e)}", flush=True)

def callback(ch, method, properties, body):
    """Callback function triggered when a message arrives from RabbitMQ."""
    data = json.loads(body)
    city = data.get("city")
    
    # תיקון: הוספת flush=True לרגע קבלת ההודעה
    print(f"[i] Received request for city: {city}", flush=True)
    
    fetch_weather(city)
    
    # אישור שההודעה טופלה בהצלחה (Acknowledge)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_worker():
    """Connects to RabbitMQ and starts consuming messages."""
    while True:
        try:
            print(f"1. Trying to connect to RabbitMQ at {RABBITMQ_HOST}...", flush=True)
            
            # תיקון קריטי: שימוש במשתנה RABBITMQ_HOST במקום במחרוזת קבועה 'rabbitmq'
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            print("2. Connected successfully!", flush=True)

            channel = connection.channel()
            print("3. Channel created.", flush=True)

            channel.queue_declare(queue='weather_requests', durable=True)
            print("4. Queue declared.", flush=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='weather_requests', on_message_callback=callback)
            print("5. Started consuming! Waiting for messages...", flush=True)

            channel.start_consuming()
        except Exception as e:
            # תיקון: הוספת flush=True לשגיאות החיבור כדי שתראי למה זה נכשל
            print(f"[!] Connection failed: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
