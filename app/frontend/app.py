from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

def fetch_weather(city_name):
    """Directly queries Open-Meteo APIs for geocoding and weather data."""
    # 1. Convert City Name -> Latitude/Longitude using Open-Meteo Geocoding
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_resp = requests.get(geo_url, params={"name": city_name, "count": 1}, timeout=5)
    geo_data = geo_resp.json()

    if not geo_data.get("results"):
        return {"error": f"City '{city_name}' not found."}

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

    return {
        "city_name": location["name"],
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "temperature": current.get("temperature"),
        "windspeed": current.get("windspeed")
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyWatch Weather</title>
    <style>
        body { font-family: sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
        form { display: flex; gap: 8px; margin-bottom: 20px; }
        input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 8px 16px; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .result { background: #f9f9f9; padding: 12px; border-radius: 4px; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🌤️ SkyWatch (Basic Flask App)</h2>
        <form method="POST">
            <input type="text" name="city" placeholder="Enter city (e.g., London, Tokyo)" required>
            <button type="submit">Search</button>
        </form>

        {% if error %}
            <div class="result error"><strong>Error:</strong> {{ error }}</div>
        {% endif %}

        {% if result %}
            <div class="result">
                <h3>{{ result.city_name }}, {{ result.country }}</h3>
                <p><strong>Temperature:</strong> {{ result.temperature }} °C</p>
                <p><strong>Wind Speed:</strong> {{ result.windspeed }} km/h</p>
                <p><strong>Lat:</strong> {{ result.latitude}} Lot:</strong> {{ result.longitude}} </p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            return render_template_string(HTML_TEMPLATE, error="Please enter a city name.")
        
        try:
            data = fetch_weather(city)
            if "error" in data:
                return render_template_string(HTML_TEMPLATE, error=data["error"])
            return render_template_string(HTML_TEMPLATE, result=data)
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, error=f"Request failed: {str(e)}")

    return render_template_string(HTML_TEMPLATE)

@app.route("/healthz")
def healthz():
    """Simple K8s readiness probe endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)