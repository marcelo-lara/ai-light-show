import { useEffect, useRef, useState } from 'preact/hooks';
import FixtureCard from './FixtureCard';
import SongArrangement from './SongArrangement';
import SongCues from './SongCues';
import AudioPlayer from './AudioPlayer'; 
import Chasers from './Chasers';

export function App() {
  const wsRef = useRef(null); // WebSocket reference
  const [wsConnected, setWsConnected] = useState(false);

  // Song metadata and playback state
  const [currentSongFile, setCurrentSongFile] = useState(); //'born_slippy.mp3'
  const [songData, setSongData] = useState();
  const [isPlaying, setIsPlaying] = useState(false);  
  const [currentTime, setCurrentTime] = useState(0);
  const [syncTime, setSyncTime] = useState(0);

  // Song Analysis state
  const [analysisResult, setAnalysisResult] = useState({});

  // DMX fixtures, presets, and cues
  const [fixtures, setFixtures] = useState([]);
  const [fixturesPresets, setFixturesPresets] = useState([]);
  const [cues, setCues] = useState([]);
  const [chasers, setChasers] = useState([]);

  // UI toast notification state
  const [toast, setToast] = useState(null);

  // Reference to fixtures to avoid stale closure issues
  const fixturesRef = useRef(fixtures);  
  useEffect(() => {
    fixturesRef.current = fixtures;
  }, [fixtures]);

  ///////////////////////////////////////////////////////
  // WebSocket connection and message handling
  const wsSend = (cmd, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: cmd, ...data
      }));
    }
  }

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log("🎵 WebSocket connected");
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "dmx_update") {
          const universe = msg.universe;
          onDmxUpdate(universe);
          return;
        }

        if (msg.type === "cuesUpdated") {
          console.log("Received cues update:", msg.cues);
          setCues(msg.cues);
        }

        if (msg.type === "analyzeResult") {
          setAnalysisResult(msg);
          setToast("Song analysis complete!");
        }

        if (msg.type === "songLoaded") {
          setCues(msg.cues || []);
          setFixtures(msg.fixtures || []);
          setFixturesPresets(msg.presets || []);
          setSongData(msg.metadata || {});
          setChasers(msg.chasers || []);
        }
      } catch (err) {
        console.error("WebSocket message error:", err);
      }
    };

    ws.onerror = (e) => console.error("WebSocket error:", e);
    ws.onclose = () => {
      console.log("WebSocket closed")
      setWsConnected(false);
    };

    return () => ws.close();
  }, []);

  // Send update when play/pause changes
  useEffect(() => {
    wsSend("sync", {isPlaying, currentTime});
  }, [isPlaying, syncTime]);

  // sync timecode with server
  useEffect(() => {
    const sec = Math.floor(currentTime);
    if (sec === syncTime) return; 
    setSyncTime(sec);
  }, [currentTime]);

  // Handle DMX updates from WebSocket
  const onDmxUpdate = (universe) => {
    const updatedFixtures = fixturesRef.current.map(fixture => {
      const newValues = {};
      for (const [key, dmxChannel] of Object.entries(fixture.channels)) {
        newValues[key] = universe[dmxChannel-1] ?? 0;
      }
      return { ...fixture, current_values: newValues };
    });
    setFixtures(updatedFixtures);
  }

  // UI toast effect ----------------------------------------
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  
  ///////////////////////////////////////////////////////
  // load song and fixtures on initial render
  useEffect(() => {
    setCurrentSongFile("born_slippy.mp3");
  }, []);

  useEffect(() => {
    if (!currentSongFile) return;
    wsSend("loadSong", { file: currentSongFile });
  }, [currentSongFile, wsConnected]);

  return (
    <div className="flex flex-row gap-2">
      {/* Main Panel */}
      <div className="w-2/3">
        <div className="p-6 bg-black text-white min-h-screen">
          <h1 className="text-3xl font-bold mb-4">🎛️ AI Light Show Designer</h1>

          {toast && (
            <div
              className="fixed top-6 left-1/2 transform -translate-x-1/2 z-50 bg-green-600 text-white px-6 py-3 rounded shadow-lg text-center transition-all duration-300"
              style={{ minWidth: 240, maxWidth: 400 }}
            >
              {toast}
            </div>
          )}

          {/* Audio Player Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <AudioPlayer 
              currentSongFile={currentSongFile} 
              onReady={()=>{}}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              analyzeSong={(data)=>{setAnalysisResult(undefined); wsSend("analyzeSong", data)}}
              analysisResult={analysisResult}
            />
          </div>

          {/* Song Cue Controls Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <SongCues 
              cues={cues}
              delCue={(cue)=>wsSend("deleteCue", {cue: cue})}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              updateCues={(cues)=>wsSend("updateCues", {cues: cues})}
            />
          </div>

          {/* Song Arrangement Controls Card */}
          <div className="bg-white/10 rounded-2xl p-6">
            <SongArrangement
              currentTime={currentTime}
              songData={songData}
              saveArrangement={(a) => {wsSend("saveArrangement", {arrangement: a})}}
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
              allPresets={fixturesPresets}
              addCue={(cue)=>wsSend("addCue", {cue: cue})}
              />
          ))
        )}

        <Chasers
          currentTime={currentTime}
          chasers={chasers}
          insertChaser={(chaserData) => wsSend("insertChaser", chaserData)}
        />

      </div>
    </div>
  );
}
