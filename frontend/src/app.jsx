import { useEffect, useRef, useState } from 'preact/hooks';
import { formatTime, saveToServer } from "./utils";
import FixtureCard from './FixtureCard';
import WaveSurfer from 'wavesurfer.js';


export function App() {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);
  const [cues, setCues] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSongFile] = useState('born_slippy.mp3');
  
  const SongsFolder = '/songs/';

  const [arrangement, setArrangement] = useState([]);
  const [editMode, setEditMode] = useState(false);

  const [toast, setToast] = useState(null);
  const [currentSection, setCurrentSection] = useState(null);

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
      });

      ws.on('audioprocess', () => {
        const time = ws.getCurrentTime();
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

  useEffect(() => {
    let current = null;
    for (let i = 0; i < arrangement.length; i++) {
      if (currentTime >= arrangement[i].time) current = i;
    }
    setCurrentSection(current);
  }, [currentTime, arrangement]);

  const updateLabel = (index, label) => {
    const updated = [...arrangement];
    updated[index].label = label;
    setArrangement(updated);
  };

  const deleteMarker = (index) => {
    const updated = [...arrangement];
    updated.splice(index, 1);
    setArrangement(updated);
  };

  const addMarker = () => {
    const time = parseFloat(currentTime.toFixed(3));
    const newMarker = { time, label: `Section ${arrangement.length + 1}` };
    setArrangement([...arrangement, newMarker]);
  };

  ///////////////////////////////////////////////////////
  useEffect(() => {
    fetch(SongsFolder + currentSongFile + ".arrangement.json")
      .then((res) => res.json())
      .then((data) => setArrangement(data))
      .catch((err) => console.error("Failed to load arrangement:", err));
  }, []);
    
  const saveArrangement = () => {
    saveToServer(currentSongFile + ".arrangement.json", arrangement, "Arrangement saved!", setToast);
  };

  ///////////////////////////////////////////////////////
  useEffect(() => {
    fetch(SongsFolder + currentSongFile + ".cues.json")
      .then((res) => res.json())
      .then((data) => setCues(data))
      .catch((err) => console.error("Failed to load Cues:", err));
  }, []);

  const saveCues = () => {
    saveToServer(currentSongFile + ".cues.json", cues, "Cues saved!", setToast);
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

    // add cue
    setCues([...cues, cue]);
  };

  useEffect(() => {
    if (fixtures.length === 0) return;

    const ws = new WebSocket(`ws://${window.location.host}/ws`);

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

  const sendDMXUpdate = async (channelMap) => {
    try {
      const res = await fetch("/dmx/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values: channelMap }),
      });
      const result = await res.json();
      console.log("sendDMX update", result);
    } catch (err) {
      console.error("DMX update failed:", err);
    }
  };

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
            <div ref={containerRef} className="mb-4" />
            <div id="song-controls" class="flex flex-col items-center">
              <div className="flex items-center gap-4 mb-4">
                <button onClick={() => wavesurferRef.current?.play()} className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">▶️ Start</button>
                <button onClick={() => wavesurferRef.current?.pause()} className="bg-yellow-500 hover:bg-yellow-600 px-4 py-2 rounded">⏸️ Pause</button>
                <button onClick={() => { wavesurferRef.current?.pause(); wavesurferRef.current?.seekTo(0); }} className="bg-gray-700 hover:bg-gray-800 px-4 py-2 rounded">⏹️ Stop</button>
                <span className="ml-4 text-gray-400">Current Time: {formatTime(currentTime)}</span>
              </div>
            </div>
          </div>

          {/* Song Cue Controls Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <div className="flex items-center gap-4 mb-4">
              <button onClick={saveCues} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save Cue</button>
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
            <div className="flex items-center gap-4 mb-4">
              <button onClick={saveArrangement} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save</button>
              <button onClick={addMarker} className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">➕ Add Marker</button>
              <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">✏️ {editMode ? 'Exit Edit Mode' : 'Edit'}</button>
            </div>

            <div className="bg-white/10 rounded p-4 text-sm">
              <h2 className="text-lg mb-2 font-semibold">Arrangement</h2>
              <ul className="space-y-1">
                {arrangement.map((section, index) => (
                  <li key={index} className={index === currentSection ? 'bg-green-700 px-2 py-1 rounded' : 'text-gray-300'}>
                    {editMode ? (
                      <div className="flex items-center gap-2">
                        <input className="text-black px-1 rounded" value={section.label} onChange={(e) => updateLabel(index, e.target.value)} />
                        <button onClick={() => deleteMarker(index)}>❌</button>
                      </div>
                    ) : (
                      <>[{formatTime(section.time)}] {section.label}</>
                    )}
                  </li>
                ))}
              </ul>
            </div>
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
              sendDMXUpdate={sendDMXUpdate}
              addCue={addCue}
              />
          ))
        )}
      </div>
    </div>
  );
}
