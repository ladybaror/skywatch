import pika
import time

credentials = pika.PlainCredentials('guest', 'guest')

parameters = pika.ConnectionParameters(
    host='localhost',
    credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
queue_name = 'weather_requests'
channel.queue_declare(queue=queue_name)
for i in range(1, 21):
    message = f"Order #{i}"
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message
    )
    print(f"Sent: {message}")
    time.sleep(1)
connection.close()
