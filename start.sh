#!/bin/bash
# Run the following:
# chmod +x start.sh
# ./start.sh
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
