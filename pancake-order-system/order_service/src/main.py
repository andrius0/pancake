from dotenv import load_dotenv
load_dotenv()
# Entry point for Order Service 
from api import app

if __name__ == "__main__":
    import uvicorn
    import os
    host = os.getenv("ORDER_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("ORDER_SERVICE_PORT", 8000))
    uvicorn.run(app, host=host, port=port) 