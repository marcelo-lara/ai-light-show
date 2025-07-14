# Song Analysis Service

A standalone microservice for audio analysis in the AI Light Show system.

## Features

- **Beat Detection**: Uses Essentia for precise beat detection and BPM analysis
- **Stem Separation**: Demucs-based audio stem separation (drums, bass, vocals, other)
- **Pattern Analysis**: Advanced clustering to identify recurring patterns in drum and bass stems
- **Chord Analysis**: Harmonic analysis and chord progression detection
- **Song Structure**: Automatic arrangement guessing based on patterns and beats

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the service and its dependencies.

### Song Analysis
```
POST /analyze
Content-Type: application/json

{
  "song_path": "/path/to/song.mp3",
  "reset_file": true,
  "debug": false
}
```

### Upload and Analyze
```
POST /analyze/upload
Content-Type: multipart/form-data

file: <audio file>
reset_file: true
debug: false
```

### Batch Analysis
```
GET /analyze/batch/{songs_folder}?reset_file=true
```

## Docker Usage

The service is designed to run as part of the AI Light Show Docker Compose stack:

```bash
# Build and run the entire stack
docker-compose up --build

# Run just the song analysis service
docker-compose up song-analysis
```

## Standalone Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

The service will be available at `http://localhost:8001`.

## Configuration

The service can be configured via environment variables:

- `PORT`: Service port (default: 8001)
- `HOST`: Service host (default: 0.0.0.0)

## Architecture

The service is built using:

- **FastAPI**: Modern async web framework
- **Essentia**: Audio analysis library for beats, BPM, and chord detection
- **Librosa**: Audio signal processing for pattern analysis
- **Demucs**: Deep learning-based audio source separation
- **Scikit-learn**: Machine learning for clustering and pattern recognition

## Integration

The main AI Light Show backend communicates with this service via HTTP API calls. The `SongAnalysisClient` class in the main backend handles the communication.

## Performance

The service is optimized for:
- Batch processing of multiple songs
- Efficient memory usage with lazy loading
- GPU acceleration for Demucs when available
- Caching of intermediate results

## Development

To add new analysis features:

1. Add your analysis function to the appropriate module in `services/audio/`
2. Update the `SongAnalyzer` class to include your analysis
3. Add API endpoints if needed
4. Update the client in the main backend if required
