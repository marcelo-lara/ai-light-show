# AI Light Show

An intelligent DMX lighting control system that uses AI to analyze music and create synchronized light shows. The system combines audio analysis, natural language processing, and real-time DMX control to automatically generate lighting performances that match the musical content.

## 🎯 Overview

AI Light Show is a proof-of-concept system that demonstrates how artificial intelligence can be used to create dynamic lighting displays synchronized to music. The system analyzes audio files to extract musical features like beats, tempo, key signatures, and chord progressions, then uses this information to generate appropriate lighting effects through DMX-controlled fixtures.

## 🏗️ Architecture

### Backend (Python/FastAPI)

The backend is built with **FastAPI** and provides a comprehensive set of APIs for audio analysis, AI processing, and DMX control.

#### Core Components

- **FastAPI Application** (`backend/main.py`): Main application entry point with CORS configuration and route management
- **DMX Controller** (`backend/dmx_controller.py`): Art-Net DMX protocol implementation for lighting fixture control
- **Timeline Engine** (`backend/timeline_engine.py`): Real-time cue execution and playback synchronization
- **Render Engine** (`backend/render_engine.py`): DMX universe rendering and fixture state management

#### AI & Audio Analysis

- **Essentia Analysis** (`backend/ai/essentia_analysis.py`): Advanced audio feature extraction including:
  - Beat detection and tempo analysis
  - Chord progression recognition
  - Key signature detection
  - Harmonic content analysis (HPCP)
  - Musical structure segmentation

- **Demucs Audio Separation** (`backend/ai/demucs_split.py`): Source separation for isolating drums, vocals, and instruments

- **Drum Classification** (`backend/ai/drums_infer.py`): ML-based drum pattern recognition and classification

- **Natural Language Processing**:
  - **Cue Interpreter** (`backend/ai/cue_interpreter.py`): Converts natural language commands into lighting dmx instructions.
  - **Ollama Integration** (`backend/ai/ollama_*.py`): Local LLM integration for intelligent lighting suggestions

#### Data Models & Services

- **Application State** (`backend/models/app_state.py`): Centralized state management
- **Song Metadata** (`backend/models/song_metadata.py`): Structured audio analysis data
- **Cue Service** (`backend/services/cue_service.py`): Lighting cue management and persistence
- **WebSocket Service** (`backend/services/websocket_service.py`): Real-time client communication

#### API Routes

- **DMX Router** (`backend/routers/dmx.py`): Fixture control and DMX universe management
- **Songs Router** (`backend/routers/songs.py`): Audio file management and analysis
- **AI Router** (`backend/routers/ai_router.py`): AI-powered lighting generation
- **WebSocket Router** (`backend/routers/websocket.py`): Real-time communication

### Frontend (Preact/Vite)

The frontend is a modern single-page application built with **Preact** and **Vite**, providing an intuitive interface for lighting design and control.

#### Key Components

- **Audio Player** (`AudioPlayer.jsx`): Waveform visualization and playback control using WaveSurfer.js
- **Chat Assistant** (`ChatAssistant.jsx`): Natural language interface for lighting control
- **Song Analysis** (`SongAnalysis.jsx`): Visual representation of audio analysis results
- **Fixtures Control** (`Fixtures.jsx`, `FixtureCard.jsx`): Manual fixture control and monitoring
- **Cue Management** (`SongCues.jsx`): Timeline-based cue editing and visualization
- **Arrangement View** (`SongArrangement.jsx`): Musical structure visualization
- **Chord Display** (`ChordsCard.jsx`): Real-time chord progression display

#### Technology Stack

- **Preact**: Lightweight React alternative for component-based UI
- **Vite**: Fast build tool and development server
- **TailwindCSS**: Utility-first CSS framework for styling
- **WaveSurfer.js**: Audio waveform visualization and interaction
- **Socket.IO**: Real-time WebSocket communication with backend
- **React Toastify**: User notification system

## 🎵 Features

### Audio Analysis
- **Beat Detection**: Precise beat tracking using multi-feature analysis
- **Tempo Analysis**: BPM detection and tempo stability analysis
- **Chord Recognition**: Real-time chord progression identification
- **Key Detection**: Musical key and scale recognition
- **Structure Analysis**: Automatic detection of verses, choruses, bridges, etc.
- **Source Separation**: Isolation of drums, vocals, and instruments

### AI-Powered Lighting
- **Natural Language Control**: Create lighting cues using plain English commands
- **Intelligent Suggestions**: AI-generated lighting recommendations based on musical content
- **Pattern Recognition**: Automatic detection of musical patterns for synchronized effects
- **Beat Synchronization**: Precise timing alignment with musical beats

### DMX Control
- **Art-Net Protocol**: Industry-standard DMX over Ethernet
- **Multi-Fixture Support**: Control various lighting fixture types (RGB and moving heads)
- **Real-time Rendering**: 60 FPS DMX universe updates
- **Preset System**: Reusable lighting effect templates
- **Chase Sequences**: Complex multi-fixture lighting patterns

### User Interface
- **Visual Timeline**: Drag-and-drop cue editing with waveform display
- **Real-time Monitoring**: Live fixture status and DMX channel values
- **Interactive Waveform**: Click-to-seek audio navigation
- **Responsive Design**: Works on desktop and tablet devices

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/marcelo-lara/ai-light-show.git
   cd ai-light-show
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Web Interface: http://localhost:5500

### Local Development

#### Backend Setup

1. **Create Python environment**:
   ```bash
   pyenv virtualenv 3.10.17 ai-light
   pyenv activate ai-light
   pyenv local ai-light
   ```

2. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the backend**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

## 📁 Project Structure

```
ai-light-show/
├── backend/                    # Python FastAPI backend
│   ├── ai/                    # AI and audio analysis modules
│   │   ├── essentia_analysis.py    # Audio feature extraction
│   │   ├── cue_interpreter.py      # Natural language processing
│   │   ├── ollama_*.py             # LLM integration
│   │   └── drums_infer.py          # Drum pattern recognition
│   ├── models/                # Data models
│   ├── routers/               # API route handlers
│   ├── services/              # Business logic services
│   ├── main.py               # FastAPI application
│   ├── dmx_controller.py     # DMX/Art-Net control
│   └── requirements.txt      # Python dependencies
├── frontend/                  # Preact/Vite frontend
│   ├── src/
│   │   ├── app.jsx           # Main application component
│   │   ├── AudioPlayer.jsx   # Audio playback and waveform
│   │   ├── ChatAssistant.jsx # AI chat interface
│   │   └── *.jsx             # Other UI components
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
├── fixtures/                  # Lighting fixture configurations
│   ├── master_fixture_config.json  # Fixture definitions
│   ├── fixture_presets.json        # Lighting presets
│   └── chaser_templates.json       # Chase sequences
├── songs/                     # Audio files directory
├── notebooks/                 # Jupyter notebooks for analysis
├── artnet_dummy/             # Art-Net testing tools
├── docker-compose.yml        # Docker services configuration
├── Dockerfile               # Container build instructions
└── README.md               # This file
```

## 🎛️ Fixture Configuration

The system supports various DMX lighting fixtures through JSON configuration files:

### Currently Supported Fixture Types
- **RGB Par Cans**: Basic color mixing fixtures
- **Moving Head Lights**: Pan/tilt with color and gobo control

### Configuration Example
```json
{
  "id": "parcan_l",
  "name": "ParCan Left",
  "type": "rgb",
  "channels": {
    "dim": 16,
    "red": 17,
    "green": 18,
    "blue": 19,
    "strobe": 20
  }
}
```

## 🤖 AI Integration

### Local LLM (Ollama)
The system integrates with Ollama for local language model processing:
- **Model**: Supports various models (Llama, Mistral, etc.)
- **Privacy**: All processing happens locally
- **Commands**: Natural language lighting control
- **Suggestions**: AI-generated lighting recommendations

### Natural Language Examples
```
"Add red flash at the drop"
"Create blue chase during the chorus"
"Set all lights to white at 2:30"
"Strobe the parcans every beat for 8 beats"
```

## 🔧 Configuration

### Environment Variables
- `ARTNET_IP`: DMX controller IP address (default: 127.0.0.1)
- `ARTNET_PORT`: Art-Net port (default: 6454)
- `OLLAMA_HOST`: Ollama server URL (default: http://backend-llm:11434)

### Audio Formats
Supported audio formats: MP3, WAV, FLAC, M4A

## 🧪 Testing & Development

### Art-Net Testing
The project includes a dummy Art-Net node for testing without physical hardware:
```bash
cd artnet_dummy
python artnet_node.py
```

### Jupyter Notebooks
Analysis notebooks are available in the `notebooks/` directory for:
- Audio feature exploration
- Drum pattern analysis
- Chord progression visualization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is a proof-of-concept and is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- **Essentia**: Audio analysis framework
- **Demucs**: Source separation model
- **Ollama**: Local LLM runtime
- **Art-Net**: DMX over Ethernet protocol
- **FastAPI**: Modern Python web framework
- **Preact**: Lightweight React alternative

## 📞 Support

For questions or issues, please open a GitHub issue or refer to the API documentation at `/docs` when running the application.
