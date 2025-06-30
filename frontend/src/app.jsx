import { useEffect, useRef, useState } from 'preact/hooks';
import FixtureCard from './FixtureCard';
import SongArrangement from './SongArrangement';
import SongCues from './SongCues';
import AudioPlayer from './AudioPlayer'; 
import SongSelector from './SongSelector';
import ChordsCard from './ChordsCard';
import Chasers from './Chasers';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import SongAnalysis from './SongAnalysis';

export function App() {
  const wsRef = useRef(null); // WebSocket reference
  const [wsConnected, setWsConnected] = useState(false);

  // Song metadata and playback state
  const [currentSongFile, setCurrentSongFile] = useState();
  const [previousSongFile, setPreviousSongFile] = useState();
  const [songData, setSongData] = useState();
  const [isPlaying, setIsPlaying] = useState(false);  
  const [currentTime, setCurrentTime] = useState(0);
  const [syncTime, setSyncTime] = useState(0);
  const [songsList, setSongsList] = useState([]);

  // Song Analysis state
  const [analysisResult, setAnalysisResult] = useState({});

  // DMX fixtures, presets, and cues
  const [fixtures, setFixtures] = useState([]);
  const [fixturesPresets, setFixturesPresets] = useState([]);
  const [cues, setCues] = useState([]);
  const [chasers, setChasers] = useState([]);

  // UI toast notification state
  const [toastMessage, setToast] = useState(null);

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
        switch (msg.type) {
          case "setup": {
            console.log("setup:", msg);
            setSongsList(msg.songs || []);
            setFixtures(msg.fixtures || []);
            setFixturesPresets(msg.presets || []);
            setChasers(msg.chasers || []);

            // load default song if not set
            setCurrentSongFile("born_slippy.mp3");

            break;
          }
          case "dmx_update": {
            const universe = msg.universe;
            onDmxUpdate(universe);
            break;
          }
          case "cuesUpdated": {
            console.log("Received cues update:", msg.cues);
            setCues(msg.cues);
            break;
          }
          case "analyzeResult": {
            console.log("Received song analysis result:", msg);
            setAnalysisResult({"status": msg.status});
            if (msg.metadata) setSongData(msg.metadata);
            setToast("Song analysis complete!");
            break;
          }
          case "songLoaded": {
            setCues(msg.cues || []);
            setSongData(msg.metadata || {});
            console.log("Song loaded:", msg.metadata);
            break;
          }
          case "syncAck": {
            // keepalive message to acknowledge sync
            break;
          }
          default:
            console.warn("Unhandled message type:", msg.type);
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
    if (toastMessage) {
      toast.success(toastMessage);
    }
  }, [toastMessage]);

  
  ///////////////////////////////////////////////////////
  // load song 
  useEffect(() => {
    if (previousSongFile == currentSongFile) return;
    setPreviousSongFile(currentSongFile);
    if (!currentSongFile) return;
    wsSend("loadSong", { file: currentSongFile });
  }, [currentSongFile, wsConnected]);

  return (
    <div className="flex flex-row gap-2">
      {/* Main Panel */}
      <div className="w-2/3">
        <div className="p-6 bg-black text-white min-h-screen">
          <h1 className="text-3xl font-bold mb-4">🎛️ AI Light Show Designer</h1>

          <ToastContainer />

          {/* Audio Player Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <AudioPlayer 
              currentSongFile={currentSongFile} 
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              analyzeSong={(data)=>{setAnalysisResult(undefined); wsSend("analyzeSong", data)}}
              analysisResult={analysisResult}
              songData={songData}
            />
          </div>
          {songData && songData?.bpm && ( 
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <SongAnalysis 
              songData={songData} 
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
            />
          </div>
          )}

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
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-1/3 text-white p-6">
        <div>
          <SongSelector 
            currentSongFile={currentSongFile} 
            songsList={songsList} 
            setCurrentSongFile={setCurrentSongFile} 
          />
        </div>

        <SongArrangement
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          songData={songData}
          saveArrangement={(a) => {wsSend("saveArrangement", {arrangement: a})}}
        />

        <div className="bg-white/10 p-2 mb-6 rounded text-white text-sm">
          <ChordsCard songData={songData} currentTime={currentTime} />
        </div>

        <div>
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
        </div>
        <div className="mt-6">
          <Chasers
            currentTime={currentTime}
            chasers={chasers}
            insertChaser={(chaserData) => wsSend("insertChaser", chaserData)}
          />
        </div>
      </div>
    </div>
  );
}
