import os
import logging
import redis
import threading
import queue
import time
import random
from flask import Flask, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_CHANNEL = os.getenv('REDIS_CHANNEL', 'orders')

app = Flask(__name__)
CORS(app)

# Global client list with thread lock
clients = []
clients_lock = threading.Lock()

def redis_listener():
    while True:
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
            pubsub = r.pubsub()
            pubsub.subscribe(REDIS_CHANNEL)
            logging.info(f"Subscribed to Redis channel: {REDIS_CHANNEL}")
            for message in pubsub.listen():
                if message.get('type') == 'message':
                    data = message['data']
                    with clients_lock:
                        for q in clients:
                            try:
                                q.put_nowait(data)
                            except queue.Full:
                                logging.warning("Client queue full. Dropping message.")
        except Exception as e:
            logging.error(f"Redis listener error: {e}. Retrying in 5s...")
            time.sleep(5)

def event_stream(q):
    heartbeat_counter = 0
    try:
        while True:
            try:
                data = q.get(timeout=1)
                yield f"data: {data.decode('utf-8') if isinstance(data, bytes) else data}\n\n"
            except queue.Empty:
                if heartbeat_counter % 5 == 0:  # Reduce heartbeat log noise
                    logging.info("Heartbeat sent to SSE client")
                yield ":ping\n\n"
                heartbeat_counter += 1
            time.sleep(0.1)
    except GeneratorExit:
        logging.info("Client disconnected (GeneratorExit)")
        with clients_lock:
            if q in clients:
                clients.remove(q)
        logging.info("Client removed from list")

@app.route('/stream')
def stream():
    q = queue.Queue(maxsize=1000)
    with clients_lock:
        clients.append(q)
    logging.info(f"Client connected. Total clients: {len(clients)}")
    return Response(stream_with_context(event_stream(q)), mimetype="text/event-stream")

@app.route('/test_stream')
def test_stream():
    def generate_random_numbers():
        while True:
            random_number = random.randint(1, 100)
            yield f"data: {random_number}\n\n"
            time.sleep(1)
    return Response(stream_with_context(generate_random_numbers()), mimetype="text/event-stream")

if __name__ == "__main__":
    try:
        t = threading.Thread(target=redis_listener, daemon=True)
        t.start()
        app.run(host="0.0.0.0", port=5001, threaded=True)
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
