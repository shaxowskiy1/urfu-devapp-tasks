import pika
import json


def send_message():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=5672, virtual_host="local")
    )
    channel = connection.channel()

    channel.queue_declare(queue='product')

    message = {
        'name': 'laptop',
    }

    channel.basic_publish(
        exchange='',
        routing_key='product',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        )
    )
    print("Сообщение отправлено:", message)
    connection.close()


if __name__ == "__main__":
    send_message()