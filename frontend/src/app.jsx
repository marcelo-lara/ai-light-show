import { useEffect, useRef, useState } from 'preact/hooks';
import { formatTime, saveToServer, SongsFolder } from "./utils";
import FixtureCard from './FixtureCard';
import SongArrangement from './SongArrangement';
import WaveSurfer from 'wavesurfer.js';


export function App() {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);
  const [cues, setCues] = useState([]);
  const wsRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);  
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSongFile] = useState('born_slippy.mp3');
  
  const [toast, setToast] = useState(null);

  const [fixtures, setFixtures] = useState([]);

  useEffect(() => {
    const setupWaveSurfer = () => {
      wavesurferRef.current = WaveSurfer.create({
        container: containerRef.current,
        waveColor: '#555',
        progressColor: '#1d4ed8',
        height: 80,
        responsive: true,
      });

      wavesurferRef.current.load(SongsFolder + currentSongFile);

      const ws = wavesurferRef.current;
      ws.on('ready', () => {
        console.log("ready ->", ws.isPlaying());
      });
      ws.on('finish', () => {
        setIsPlaying(false);
        console.log("finish ->", ws.isPlaying());
      });
      ws.on('pause', () => {
        setIsPlaying(false);
        const time = ws.getCurrentTime();
        setCurrentTime(time);
      });

      ws.on('play', () => {
        const time = ws.getCurrentTime();
        console.log("play -> time:", time);
        setIsPlaying(true);
      });

      ws.on('audioprocess', () => {
        const time = ws.getCurrentTime();
        setCurrentTime(time);
      });

      ws.on('seeking', () => {
        const time = ws.getCurrentTime();
        console.log("seeking -> time:", time);
        setCurrentTime(time);
      });

    };

    if (document.readyState === 'complete') {
      setupWaveSurfer();
    } else {
      window.addEventListener('load', setupWaveSurfer);
      return () => window.removeEventListener('load', setupWaveSurfer);
    }
  }, []);

  useEffect(() => {
    const loadFixtures = async () => {
      try {
        const res = await fetch("/fixtures/master_fixture_config.json");
        if (!res.ok) throw new Error("Fixture config not found");
        const data = await res.json();
        setFixtures(data);
        console.log("Loaded fixtures:", data);
      } catch (err) {
        console.error("Failed to load fixture config:", err);
      }
    };

    loadFixtures();
  }, []);


  ///////////////////////////////////////////////////////

  // Load cues from server
  useEffect(() => {
    fetch(SongsFolder + currentSongFile + ".cues.json")
      .then((res) => res.json())
      .then((data) => setCues(Array.isArray(data) ? data.sort((a, b) => (a.time ?? 0) - (b.time ?? 0)) : []))
      .catch((err) => console.error("Failed to load Cues:", err));
  }, []);

  const saveCues = () => {
    saveToServer(currentSongFile + ".cues.json", cues, "Cues saved!", setToast);
  };

  const renderCues = async (fileName) => {
    try {
      const res = await fetch("/renderSong", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fileName: currentSongFile }),
      });
      const result = await res.json();
      if (result.status === "ok") {
        setToast("Song rendered successfully");
      } else {
        setToast("Failed to render song");
      }
    } catch (err) {
      console.error("Request failed:", err);
      setToast("Error rendering song");
    }
  };

  const addCue = (cue) => {
    // calculate cue overall event time
    if (cue.parameters){
      if (cue.parameters.loop_duration) {
        cue.duration = parseFloat((cue.parameters.loop_duration).toFixed(3));
      } else {
        cue.duration = parseFloat((cue.parameters.fade_duration || 0).toFixed(3));
      }
    }

    // add cue and place in time
    const newCues = [...cues, cue].sort((a, b) => (a.time ?? 0) - (b.time ?? 0));
    setCues(newCues);
  };

  useEffect(() => {
    if (fixtures.length === 0) return;

    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log("🎵 WebSocket connected");
      ws.send(JSON.stringify({ isPlaying, currentTime }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "dmx_update") {
          const universe = data.universe;
          const updatedFixtures = fixtures.map(fixture => {
            const newValues = {};
            for (const [key, dmxChannel] of Object.entries(fixture.channels)) {
              newValues[key] = universe[dmxChannel-1] ?? 0;
            }
            return { ...fixture, current_values: newValues };
          });
          console.log("Received DMX:", universe);
          setFixtures(updatedFixtures);
        }
      } catch (err) {
        console.error("WebSocket message error:", err);
      }
    };

    ws.onerror = (e) => console.error("WebSocket error:", e);
    ws.onclose = () => console.log("WebSocket closed");

    return () => ws.close();
  }, [fixtures.length]);

  // Send update when play/pause changes
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ isPlaying, currentTime }));
    }
  }, [isPlaying]);



  // UI toast effect ----------------------------------------
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  return (
    <div className="flex flex-row gap-6">
      {/* Main Panel */}
      <div className="w-2/3">
        <div className="p-6 bg-black text-white min-h-screen">
          <h1 className="text-3xl font-bold mb-4">🎛️ AI Light Show Designer</h1>

          {toast && <div className="mb-4 p-2 bg-green-600 text-white rounded text-center">{toast}</div>}

          {/* Audio Player Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <div ref={containerRef} className="mb-4"/>
            <div id="song-controls" class="flex flex-col items-center">
              <div className="flex items-center gap-4 mb-4">
                {isPlaying ? 
                  (<button onClick={() => wavesurferRef.current?.pause()} className="bg-yellow-500 hover:bg-yellow-600 px-4 py-2 rounded">⏸️ Pause</button>) : 
                  (<button onClick={() => wavesurferRef.current?.play()} className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">▶️ Start</button>)
                }
                <button onClick={() => { wavesurferRef.current?.pause(); wavesurferRef.current?.seekTo(0); }} className="bg-gray-700 hover:bg-gray-800 px-4 py-2 rounded">⏹️ Stop</button>
                <span className="ml-4 w-6 text-gray-400">{formatTime(currentTime)}</span>
              </div>
            </div>
          </div>

          {/* Song Cue Controls Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <button onClick={saveCues} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save Cue</button>
              <button onClick={renderCues} className="bg-gray-700 hover:bg-gray-800 px-4 py-2 rounded">⚙️ Render Cue</button>
            </div>

            <div className="bg-white/10 rounded p-4 text-sm max-h-64 overflow-y-scroll">
              <h2 className="text-lg mb-2 font-semibold">Cue List</h2>
              {cues.length === 0 && (<div className="italic text-gray-400">No cues recorded yet.</div>)}
              <ul className="list-disc pl-5 space-y-1">
                {cues.map((cue, index) => (
                  <li key={index}>[{cue.time}s] {cue.fixture} → {cue.preset} ({cue.duration})</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Song Arrangement Controls Card */}
          <div className="bg-white/10 rounded-2xl p-6">
            <SongArrangement
              currentTime={currentTime}
              currentSongFile={currentSongFile}
              setToast={setToast}
            />
          </div>

        </div>
      </div>

      {/* Fixture Panel */}
      <div className="w-1/3 bg-white/10 text-white p-6 rounded-2xl">
        <h2 className="text-2xl font-bold mb-4">Fixtures</h2>
        {fixtures.length === 0 ? (
          <div className="text-sm text-gray-500 italic">No fixtures loaded</div>
        ) : (
          fixtures.map((fixture) => (
            <FixtureCard 
              key={fixture.id} 
              fixture={fixture}
              currentTime={currentTime}
              addCue={addCue}
              />
          ))
        )}
      </div>
    </div>
  );
}
