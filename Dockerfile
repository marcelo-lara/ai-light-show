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
RUN pip install \
            fastapi \
            uvicorn[standard] \
            python-multipart \
            python-osc \
            librosa \
            soundfile            

EXPOSE 5000
#ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
#HEALTHCHECK CMD curl --fail http://localhost:5000/status || exit 1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]