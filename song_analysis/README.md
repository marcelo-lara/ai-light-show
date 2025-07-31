
# ⚡️ LLM/Copilot Guidance

> **For Copilot, GPT-4, and other LLM agents:**
>
> - **Code Structure:**
>   - Main API: `app.py` (FastAPI endpoints)
>   - Core analysis: `services/audio_analyzer.py`, `services/beats_rms_flux.py`, `services/audio/`
>   - Data models: `shared/models/song_metadata.py`
> - **Entry Points:**
>   - Use function/class docstrings and `# LLM:` comments for context.
>   - For beats/RMS/flux: see `analyze_beats_rms_flux` in `services/beats_rms_flux.py`.
>   - For full song analysis: see `SongAnalyzer.analyze` in `services/audio_analyzer.py`.
> - **Efficiency:**
>   - Avoid reading large files unless necessary; prefer docstrings and summary comments.
>   - Use API endpoints for most tasks (see below).
>   - Caching is used throughout; check for `.pkl` or cached results before re-analysis.
> - **When editing:**
>   - Add/maintain concise docstrings and `# LLM:` comments for all functions/classes.
>   - Keep comments high-level and focused on intent/data flow.
> - **Code rules**
>   - Get file paths from `shared/models/song_metadata.py`. Do not hardcode paths.

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

### Beats, RMS, and Flux Analysis
```
POST /analyze
Content-Type: application/json

{
  "song_path": "/path/to/song.mp3",
  "force": false,              // Optional: force re-analysis even if cache exists
  "start_time": 0.0,           // Optional: start time in seconds for filtering
  "end_time": null             // Optional: end time in seconds for filtering
}
```

This endpoint extracts beats, RMS (volume), and spectral flux from audio files with intelligent caching:

- **Caching**: Results are saved as `.pkl` files with pandas DataFrames for fast subsequent access
- **Filtering**: Optional `start_time` and `end_time` parameters to extract specific time ranges
- **Performance**: Cached requests are significantly faster than initial analysis
- **Returns**: Only the extracted data arrays (beats, rms, flux), not the cached file

**Response Format:**
```json
{
  "status": "ok",
  "beats": [0.487, 0.493, 0.499, ...],     // Array of beat times in seconds
  "rms": [0.002085, 0.002146, ...],        // Array of RMS values for each frame
  "flux": [0.0, 0.001305, 0.001493, ...]   // Array of spectral flux values
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Analysis failed: <error description>"
}
```

### Full Song Analysis
```
POST /analyze_song
Content-Type: application/json

{
  "song_name": "song.mp3",
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

## Usage Examples

### Basic Beats/RMS/Flux Extraction

```python
import requests

# Analyze entire song
response = requests.post('http://localhost:8001/analyze', json={
    'song_path': '/path/to/song.mp3',
    'force': True  # Force new analysis
})

data = response.json()
print(f"Found {len(data['beats'])} beats")
print(f"RMS values: {len(data['rms'])} frames")
print(f"Flux values: {len(data['flux'])} frames")
```

### Time-Range Filtering

```python
# Analyze only the first 30 seconds
response = requests.post('http://localhost:8001/analyze', json={
    'song_path': '/path/to/song.mp3',
    'start_time': 0.0,
    'end_time': 30.0,
    'force': False  # Use cache if available
})

data = response.json()
print(f"First 30s: {len(data['beats'])} beats")
```

### Performance Comparison

```python
import time

# First request (creates cache)
start = time.time()
response1 = requests.post('http://localhost:8001/analyze', json={
    'song_path': '/path/to/song.mp3', 'force': True
})
duration1 = time.time() - start

# Second request (uses cache)
start = time.time()
response2 = requests.post('http://localhost:8001/analyze', json={
    'song_path': '/path/to/song.mp3', 'force': False
})
duration2 = time.time() - start

print(f"Analysis: {duration1:.2f}s, Cache: {duration2:.2f}s")
print(f"Speedup: {duration1/duration2:.1f}x faster")
```

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
- **Pandas**: DataFrame-based caching system for analysis results

### Analysis Pipeline

The `/analyze` endpoint implements a streamlined pipeline:

1. **Input Validation**: Checks file existence and parameter validity
2. **Cache Check**: Looks for existing `.pkl` files unless `force=true`
3. **Audio Loading**: Uses Essentia MonoLoader for consistent audio processing
4. **Feature Extraction**:
   - Beat detection via Essentia RhythmExtractor2013
   - Frame-by-frame RMS calculation for volume analysis
   - Spectral flux computation for onset detection
5. **Data Processing**: Synchronizes beat markers with time frames
6. **Caching**: Saves results as pandas DataFrame in pickle format
7. **Filtering**: Applies time-based filtering if requested
8. **Response**: Returns only the requested data arrays

## Integration

The main AI Light Show backend communicates with this service via HTTP API calls. The `SongAnalysisClient` class in the main backend handles the communication.

## Performance

The service is optimized for:
- **Batch processing** of multiple songs
- **Efficient memory usage** with lazy loading
- **GPU acceleration** for Demucs when available
- **Intelligent caching** of analysis results
  - Beats/RMS/flux analysis results cached as `.pkl` files with pandas DataFrames
  - Cache bypass available with `force: true` parameter
  - Significant speedup on subsequent requests (typically 10-50x faster)
  - Automatic cache invalidation when source files change
- **Frame-level analysis** with configurable time resolution for precise audio feature extraction

## Development

To add new analysis features:

1. Add your analysis function to the appropriate module in `services/audio/`
2. Update the `SongAnalyzer` class to include your analysis
3. Add API endpoints if needed
4. Update the client in the main backend if required
