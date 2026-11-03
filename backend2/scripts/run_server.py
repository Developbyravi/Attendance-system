import os
import sys
import uvicorn

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8002, reload=True)

