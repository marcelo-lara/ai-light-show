# Song Analysis Service

A standalone microservice for audio analysis in the AI Light Show system.

## Features

- **Beat Detection**: Uses Essentia for precise beat detection and BPM analysis
- **Stem Separation**: Demucs-based audio stem separation (drums, bass, vocals, other)
- **Pattern Analysis**: Advanced clustering to identify recurring patterns in drum and bass stems
- **Chord Analysis**: Harmonic analysis and chord progression detection
- **Song Structure**: Automatic arrangement guessing based on patterns and beats
- **LangGraph Pipeline**: Modular, traceable analysis pipeline with LLM-based segment labeling and lighting hint generation

## LangGraph Pipeline

The service now features a modular LangGraph-based pipeline for more traceable and maintainable audio analysis:

1. **Stem Split**: Separates audio into drums, bass, vocals, and other stems
2. **Beat Detection**: Identifies beats and tempo using Essentia
3. **Pattern Analysis**: Finds recurring patterns and segments in the audio
4. **Segment Labeler**: Uses LLM to label segments as Intro, Verse, Chorus, etc.
5. **Lighting Hint Generator**: Uses LLM to suggest creative lighting effects for each segment

The pipeline logs each node's input/output to JSON files for easier debugging and comes with a robust fallback to traditional analysis if needed.

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

## Pipeline Testing

To test the LangGraph pipeline directly:

```bash
python -m song_analysis.test_pipeline_run --song <song_name.mp3>
```

For a simplified version that works even without LangGraph installed:

```bash
python -m song_analysis.test_simple_pipeline --song <song_name.mp3>
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
