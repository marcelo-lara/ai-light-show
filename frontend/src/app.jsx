import { useEffect, useRef, useState } from 'preact/hooks';
import { formatTime, saveToServer, SongsFolder } from "./utils";
import FixtureCard from './FixtureCard';
import SongArrangement from './SongArrangement';
import WaveSurfer from 'wavesurfer.js';


export function App() {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);
  const wsRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);  
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSongFile] = useState('born_slippy.mp3');
  const [songData, setSongData] = useState();

  const [cues, setCues] = useState([]);
  const [newCue, setNewCue] = useState({ fixture: "", preset: "", time: 0, duration: 1 });
  const [editCueId, setEditCueId] = useState(null);

  const [toast, setToast] = useState(null);
  const [wsConnected, setWsConnected] = useState(null);

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
  // load song metadata
  useEffect(() => {
    fetch(SongsFolder + currentSongFile + ".metadata.json")
      .then((res) => res.json())
      .then((data) => setSongData(data))
      .catch((err) => console.error("Failed to load SongMetadata:", err));
  }, [currentSongFile]);

  const loadSong = () => {
    // Push cue changes to backend via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "loadSong",
        file: currentSongFile,
      }));
    }
    console.log("request loading song:", currentSongFile);
   }

   useEffect(() => {
    if (!wsConnected) return;
    loadSong();
  }, [currentSongFile, wsConnected]);

  const addCue = (cue) => {
    // Push cue changes to backend via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "addCue",
        cue: cue
      }));
    }
  };

  useEffect(() => {
    if (fixtures.length === 0) return;

    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log("🎵 WebSocket connected");
      setWsConnected(true);
      ws.send(JSON.stringify({ isPlaying, currentTime }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "dmx_update") {
          const universe = msg.universe;
          const updatedFixtures = fixtures.map(fixture => {
            const newValues = {};
            for (const [key, dmxChannel] of Object.entries(fixture.channels)) {
              newValues[key] = universe[dmxChannel-1] ?? 0;
            }
            return { ...fixture, current_values: newValues };
          });
          console.log("Received DMX:", universe);
          setFixtures(updatedFixtures);
          return;
        }

        if (msg.type === "cuesUpdated") {
          console.log("Received cues update:", msg.cues);
          setCues(msg.cues);
        }

        if (msg.type === "songLoaded") {
          console.log("-> songLoaded:")
          console.log('   cues:', msg.cues);
          setCues(msg.cues || []);
        }
      } catch (err) {
        console.error("WebSocket message error:", err);
      }
    };

    ws.onerror = (e) => console.error("WebSocket error:", e);
    ws.onclose = () => {
      setWsConnected(false);
      console.log("WebSocket closed")
    };

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
    <div className="flex flex-row gap-2">
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
            <h2 className="text-xl font-semibold mb-4">🎯 Song Cue Controls</h2>

            <table className="text-sm w-full text-white">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left">time</th>
                  <th className="text-left">Fixture</th>
                  <th className="text-left">Preset</th>
                  <th className="text-left">Duration</th>
                  <th className="text-left">Parameters</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cues.map((cue, idx) => (
                  <tr key={`${cue.fixture}-${cue.time}`} className="border-b border-white/10">
                    <td>{cue.time?.toFixed(2)}</td>
                    <td>{cue.fixture}</td>
                    <td>{cue.preset}</td>
                    <td>{cue.duration?.toFixed(2)}</td>
                    <td>
                      {cue.parameters && Object.entries(cue.parameters).map(([k, v]) => (
                        <span key={k} className="inline-block mr-2">{k}: {v}</span>
                      ))}
                    </td>
                    <td className="flex gap-2">
                      <button onClick={() => {
                        wsRef.current?.send(JSON.stringify({ type: "deleteCue", cue: cue }));
                      }} className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
      <div className="w-1/3 text-white p-6">
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
