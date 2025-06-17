# Stage 1: Build the frontend
FROM node:18 AS frontend
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build

# Stage 2: Serve frontend + Flask backend
FROM python:3.10-slim AS backend
WORKDIR /app

# Copy backend and static frontend
COPY backend/ ./backend/
COPY --from=frontend /app/dist ./static/

# Install Flask + python-osc
RUN pip install flask python-osc

EXPOSE 5000
CMD ["python", "backend/main.py"]