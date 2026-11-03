from flask import Flask, render_template_string, request, jsonify
import pika
import os
import json

app = Flask(__name__)

# כתובת ה-RabbitMQ (יכולה להגיע מ-Environment Variable או ברירת מחדל ללוקאל)
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")

def publish_to_queue(city_name):
    """Publishes a city search request to RabbitMQ queue."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    
    # Create a queue weather_requests if not exist
    channel.queue_declare(queue='weather_requests', durable=True)
    
    message = json.dumps({"city": city_name})
    channel.basic_publish(
        exchange='',
        routing_key='weather_requests',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # הופך את ההודעה לפריסיסטנטית (שלא תימחק באתחול)
        ))
    connection.close()


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
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🌤️ SkyWatch (Async Queue Architecture)</h2>
        <form method="POST">
            <input type="text" name="city" placeholder="Enter city (e.g., London, Tokyo)" required>
            <button type="submit">Submit Request</button>
        </form>

        {% if error %}
            <div class="result error"><strong>Error:</strong> {{ error }}</div>
        {% endif %}

        {% if success %}
            <div class="result success"><strong>Success:</strong> {{ success }}</div>
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
            publish_to_queue(city)
            return render_template_string(HTML_TEMPLATE, success=f"City '{city}' was successfully sent to the processing queue!")
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, error=f"Failed to queue request: {str(e)}")

    return render_template_string(HTML_TEMPLATE)

@app.route("/healthz")
def healthz():
    """Simple K8s readiness probe endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)