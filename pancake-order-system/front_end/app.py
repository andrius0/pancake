from flask import Flask, render_template
import os

app = Flask(__name__)


@app.route('/')
def home():
    sse_url = os.getenv('STATUS_SERVICE_SSE_URL', '/stream') # Default to /stream if not set
    order_service_url = os.getenv('ORDER_SERVICE_URL', 'http://localhost:8000') # Get Order Service URL from env var
    return render_template('index.html', sse_url=sse_url, order_service_url=order_service_url)


if __name__ == '__main__':
    app.run(port=5002)
