import { useEffect, useRef, useState } from 'preact/hooks';
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
        loadArrangement();
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

  const loadArrangement = async () => {
    const arrangementFile = SongsFolder + currentSongFile + ".arrangement.json";
    try {
      const res = await fetch(arrangementFile);
      if (!res.ok) throw new Error("Not found");
      const data = await res.json();
      if (data.arrangement && Array.isArray(data.arrangement)) {
        const arr = [...data.arrangement]
        setArrangement(arr);
        console.log("Arrangement loaded from file:", arr);
      }
      console.log("Arrangement loaded:", arrangement);
    } catch (err) {
      console.log("No arrangement file found, using default/empty.");
      setArrangement([]);
    }
  };

  const saveArrangement = () => {
    const fileName = `${currentSongFile}.arrangement.json`;
    fetch(SongsFolder + "save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: fileName, data: { arrangement } })
    })
      .then(res => res.ok ? setToast("Arrangement saved!") : setToast("Failed to save."))
      .catch(err => {
        console.error("Save error:", err);
        setToast("Save failed.");
      });
  };

  const addCue = () => {
    const time = wavesurferRef.current?.getCurrentTime().toFixed(3);
    const newCue = {
      time,
      action: 'fade_rgb',
      target: 'par_1',
      color: [255, 0, 0],
    };
    setCues([...cues, newCue]);
  };

  const downloadCues = () => {
    const blob = new Blob([JSON.stringify({ cues }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentSongFile}.cues.json`;
    a.click();
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = (time % 60).toFixed(3).padStart(6, '0');
    return `${minutes}:${seconds}`;
  };


  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  return (
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
          <button onClick={addCue} className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">🟥 Record Cue</button>
          <button onClick={downloadCues} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">💾 Download Cues</button>
          <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">✏️ {editMode ? 'Exit Edit Mode' : 'Edit Arrangement'}</button>
        </div>

        <div className="bg-white/10 rounded p-4 text-sm max-h-64 overflow-y-scroll">
          <h2 className="text-lg mb-2 font-semibold">Cue List</h2>
          {cues.length === 0 && (<div className="italic text-gray-400">No cues recorded yet.</div>)}
          <ul className="list-disc pl-5 space-y-1">
            {cues.map((cue, index) => (
              <li key={index}>[{cue.time}s] {cue.action} → {cue.target} → {JSON.stringify(cue.color)}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Song Arrangement Controls Card */}
      <div className="bg-white/10 rounded-2xl p-6">
        <div className="flex items-center gap-4 mb-4">
          <button onClick={saveArrangement} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save to Server</button>
          <button onClick={addMarker} className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">➕ Add Marker</button>
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
  );
}
