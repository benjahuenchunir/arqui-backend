"""Example of RabbitMQ receiver."""

import os
import sys

import pika
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("JOBS_USER")
PASS = os.getenv("JOBS_PASSWORD")


def main():
    """Main function."""
    if not USER or not PASS:
        raise ValueError("JOBS_USER or JOBS_PASSWORD environment variables not set")
    credentials = pika.PlainCredentials(USER, PASS)
    params = pika.ConnectionParameters(host="localhost", credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue="hello")

    def callback(ch, method, properties, body):  # pylint: disable=unused-argument
        print(f" [x] Received {body}")

    channel.basic_consume(queue="hello", on_message_callback=callback, auto_ack=True)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
