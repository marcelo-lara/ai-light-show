# AI Light Show

An intelligent lighting control system that analyzes music and creates synchronized light shows using AI and audio analysis.

## Architecture

The system consists of several microservices:

### 🎛️ Main Application (`ai-light-show`)
- **FastAPI** backend with WebSocket support for real-time communication
- **React/Preact** frontend for controlling lights and visualizing music
- **DMX** lighting control with fixture management
- **OSC** integration for external control
- **Ollama** integration for AI-powered lighting suggestions

### 🎵 Song Analysis Service (`song-analysis`)
- **Standalone microservice** for audio analysis
- **Essentia** for beat detection, BPM analysis, and chord detection
- **Demucs** for AI-powered audio stem separation
- **Librosa + Scikit-learn** for pattern detection and clustering
- **FastAPI** REST API for analysis requests
- **Intelligent caching** with pandas DataFrames for optimized performance
- **Time-based filtering** for precise audio segment analysis

### 🤖 LLM Backend (`llm-service`)
- **Ollama** service for AI language model capabilities
- GPU acceleration support
- Model management and inference
- load models (more at https://ollama.com/library)
   ```bash
   nohup /root/.ollama/pull_models.sh > /tmp/ollama-download.log 2>&1 &
   tail -f /tmp/ollama-download.log
   ```

## Features

### 🎧 Audio Analysis
- **Beat Detection**: Precise beat tracking using Essentia
- **BPM Analysis**: Automatic tempo detection
- **Stem Separation**: AI-powered separation of drums, bass, vocals, and other instruments
- **Pattern Recognition**: Clustering algorithm to identify recurring patterns
- **Chord Analysis**: Harmonic analysis and chord progression detection
- **Song Structure**: Automatic arrangement detection (verse, chorus, bridge, etc.)
- **Real-time Analysis**: Fast beats/RMS/flux extraction with intelligent caching
- **Time-based Filtering**: Extract analysis data for specific time ranges

### 💡 Lighting Control
- **DMX Protocol**: Standard DMX512 control for professional lighting
- **Fixture Management**: Support for various light fixture types
- **Real-time Control**: WebSocket-based real-time lighting updates
- **Pattern Synchronization**: Music-synchronized lighting patterns
- **Manual Override**: Direct control of individual fixtures
- **Preset Management**: Save and recall lighting presets
- **Direct Commands**: Control lighting with #action commands in chat

### 🎨 User Interface
- **AI Chat**: Natural language lighting control and suggestions
- **Real-time Visualization**: Audio waveform with beat markers
- **Interactive Timeline**: Click to seek, visual pattern display
- **Fixture Control**: Intuitive sliders and controls for each light
- **Song Library**: Manage and analyze your music collection
- **Pattern Visualization**: See detected patterns and clusters
- **Direct Commands**: Use #action commands in chat for precise control

## Quick Start

### Prerequisites
- **Docker** and **Docker Compose**
- **Git**
- Audio files in MP3 format
- DMX interface (optional, for actual lighting control)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-light-show
   ```

2. **Add your music**
   ```bash
   # Place your MP3 files in the songs/ directory
   cp your-music.mp3 songs/
   ```

3. **Configure fixtures** (optional)
   ```bash
   # Edit fixtures/fixtures.json to match your lighting setup
   # Default configuration includes sample fixtures
   ```

4. **Start the system**
   ```bash
   docker-compose up --build
   ```

5. **Access the interface**
   - Open http://localhost:5500 in your browser
   - Select a song from the library
   - Click "Analyze Song" to process the audio
   - Control lights and explore the interface

### Development Setup

For development with live reloading:

```bash
# Start just the analysis service and LLM
docker-compose up song-analysis llm-service

# Run the main app in development mode
cd backend
pip install -r requirements.txt
python main.py

# In another terminal, run the frontend
cd frontend
npm install
npm run dev
```

## Usage

### Song Analysis

1. **Upload or select** a song from your library
2. **Click "Analyze Song"** to extract beats, patterns, and structure
3. **View results** in the analysis panel:
   - Beat timeline with volume visualization
   - Detected patterns and clusters
   - Song arrangement sections
   - Chord progressions (if detected)

### Fast Audio Analysis

API to provide beats, RMS, and flux data to Agents for precise control:
```python
import requests

# Quick analysis with caching
response = requests.post('http://localhost:8001/analyze', json={
    'song_name': 'your-song',  # Song name without .mp3 extension
    'force': False,            # Use cache if available
    'start_time': 0.0,         # Optional: analyze from 0 seconds
    'end_time': 30.0           # Optional: analyze to 30 seconds
})

data = response.json()
beats = data['beats']    # Beat times in seconds (0.001 accuracy)
rms = data['rms']        # Volume levels
flux = data['flux']      # Spectral flux values
```

**Performance Benefits:**
- First analysis: ~10-30 seconds depending on song length
- Cached requests: ~0.1-0.5 seconds (10-50x faster)
- Time filtering: Extract specific segments without re-analysis

### Lighting Control

1. **Manual Control**: Use sliders to adjust individual fixtures
2. **Pattern Sync**: Enable pattern synchronization for automatic lighting
3. **AI Suggestions**: Chat with the AI for lighting recommendations
4. **Direct Commands**: Use #action commands for precise control
5. **Presets**: Save and load lighting configurations
6. **Real-time**: All changes are applied instantly via WebSocket

### Batch Processing

Analyze multiple songs at once:

```bash
# Using the service (recommended)
python backend/song_analyze_batch_service.py /path/to/songs

# Check service health
python backend/health_check_service.py
```

## Configuration

### Environment Variables

- `SONG_ANALYSIS_SERVICE_URL`: URL of the song analysis service (default: http://song-analysis:8001)
- `OLLAMA_URL`: URL of the Ollama service (default: http://llm-service:11434)
- `DMX_INTERFACE`: DMX interface type (artnet, usb, etc.)

### Fixture Configuration

Edit `fixtures/fixtures.json` to define your lighting setup:

```json
{
  "fixtures": [
    {
      "id": "parcan_1",
      "name": "Par Can 1",
      "type": "rgb",
      "channels": {
        "red": 1,
        "green": 2,
        "blue": 3,
        "dimmer": 4
      },
      "position": [0, 0, 3]
    }
  ]
}
```

## API Reference

### Song Analysis Service

- `GET /health` - Service health check
- `POST /analyze` - Extract beats, RMS, and flux with caching
- `POST /analyze_song` - Full song analysis with patterns and structure
- `POST /analyze/upload` - Upload and analyze
- `GET /analyze/batch/{folder}` - Batch analysis
- `GET /songs` - List available songs

### Main Application

- `WebSocket /ws` - Real-time communication
- `GET /songs` - List available songs
- `GET /fixtures` - Get fixture configuration
- `POST /dmx/update` - Update DMX values

## Development

### Project Structure

```
ai-light-show/
├── backend/                 # Main FastAPI application
│   ├── services/           # Backend services
│   ├── models/             # Data models
│   └── routers/            # API routes
├── frontend/               # React/Preact frontend
│   ├── src/                # Source code
│   └── public/             # Static assets
├── song_analysis/          # Standalone analysis service
│   ├── services/           # Analysis modules
│   ├── models/             # Data models
│   └── Dockerfile          # Service container
├── fixtures/               # Lighting fixture definitions
├── songs/                  # Music library
└── docker-compose.yml      # Service orchestration
```

### Adding New Analysis Features

1. **Create analysis module** in `song_analysis/services/audio/`
2. **Update SongAnalyzer** to include your analysis
3. **Add API endpoints** if needed
4. **Update the client** in the main backend

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Troubleshooting

### Service Issues

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs song-analysis
docker-compose logs ai-light-show

# Health check
python backend/health_check_service.py
```

### Common Problems

- **Song Analysis Service Unreachable**: Check that the service is running and accessible
- **GPU Issues**: Ensure Docker has GPU access configured for Demucs
- **Memory Issues**: Large audio files may require more RAM for analysis
- **DMX Issues**: Verify your DMX interface configuration
- **Cache Issues**: 
  - Delete `.pkl` files in `songs/data/` folder to force re-analysis
  - Use `force: true` parameter to bypass cache for specific requests
  - Check disk space if cache files are not being created

## Performance Tips

- **Use shorter audio clips** for faster analysis during development
- **Enable GPU** for Demucs if available
- **Batch process** multiple songs during off-peak hours
- **Cache results** - analysis results are saved automatically as `.pkl` files
- **Use the fast `/analyze` endpoint** for beats/RMS/flux when you don't need full song structure
- **Filter by time** - extract specific segments without re-analyzing entire songs
- **Monitor cache usage** - cached requests are 10-50x faster than initial analysis

## License

[Add your license information here]

## Acknowledgments

- **Essentia** - Audio analysis framework
- **Demucs** - AI audio source separation
- **FastAPI** - Modern web framework
- **React/Preact** - User interface framework
- **Ollama** - Local LLM hosting


## Test prompts

```text
use the parcans to fade blue from left to right, and then right to left during the intro
```
