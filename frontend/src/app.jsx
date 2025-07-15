import { useEffect, useRef, useState } from 'preact/hooks';
import FixtureCard from './components/fixtures/FixtureCard';
import AudioPlayer from './AudioPlayer'; 
import SongSelector from './components/song/SongSelector';
import Fixtures from './components/fixtures/Fixtures';
import ActionsCard from './components/ActionsCard';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import ChatAssistant from './ChatAssistant';
import SongMetadata from './components/SongMetadata';

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
  const [seekToTime, setSeekToTime] = useState(0);

  // model chat
  const [lastResponse, setLastResponse] = useState(null);

  // Song Analysis state
  const [analysisResult, setAnalysisResult] = useState({});

  // Listen for reset analysis result event
  useEffect(() => {
    const handleResetAnalysisResult = () => setAnalysisResult(undefined);
    window.addEventListener('resetAnalysisResult', handleResetAnalysisResult);
    return () => window.removeEventListener('resetAnalysisResult', handleResetAnalysisResult);
  }, []);

  // Lighting actions state
  const [lightingActions, setLightingActions] = useState([]);

  // DMX fixtures and presets
  const [fixtures, setFixtures] = useState([]);
  const [fixturesPresets, setFixturesPresets] = useState([]);

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

            // load default song if not set
            setCurrentSongFile("born_slippy.mp3");

            break;
          }
          case "dmx_update": {
            const universe = msg.universe;
            onDmxUpdate(universe);
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
            // DEPRECATED: setCues removed - cue system deprecated
            setSongData(msg.metadata || {});
            console.log("Song loaded:", msg.metadata);
            break;
          }
          case "fixturesUpdated": {
            console.log("Received fixtures update:", msg);
            setFixtures(msg.fixtures || []);
            setFixturesPresets(msg.presets || []);
            setToast("Fixtures updated!");
            break;
          }
          case "syncAck": {
            // keepalive message to acknowledge sync
            break;
          }
          case "actionsUpdate": {
            // Handle lighting actions updates from backend
            console.log("Received actions update:", msg);
            setLightingActions(msg.actions || []);
            break;
          }
          case "chatResponse": {
            setLastResponse(msg.response || "(no response?)");
            break;
          }
          case "chatResponseStart": {
            if (window._chatAssistantStartStreaming) {
              window._chatAssistantStartStreaming();
            }
            break;
          }
          case "chatResponseChunk": {
            if (msg.chunk && window._chatAssistantAppendChunk) {
              window._chatAssistantAppendChunk(msg.chunk);
            }
            break;
          }
          case "chatResponseEnd": {
            if (window._chatAssistantEndStreaming) {
              window._chatAssistantEndStreaming();
            }
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

  function handleSeekTo(time) {
    setSeekToTime(time);
  }

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
              songData={songData}
              seekTo={seekToTime}
              onStop={() => {
                wsSend("blackout", {});
              }}
            />
          </div>

          {/* Chat Card */}
          <div className="bg-white/10 rounded-2xl p-6 mb-6">
            <ChatAssistant 
              wsSend={wsSend} 
              lastResponse={lastResponse}
            />
          </div>

          {/* Actions Card: Display lighting actions from the backend */}
          <ActionsCard wsActions={lightingActions} />

        </div>
      </div>

      {/* Right Panel */}
      <div className="w-1/3 text-white p-6 space-y-6">

        {/* Song Selection */}
        <div>
          <SongSelector 
            currentSongFile={currentSongFile} 
            songsList={songsList} 
            setCurrentSongFile={setCurrentSongFile} 
          />
        </div>

        {/* Song Metadata Components */}
        {songData && (
          <SongMetadata
            currentTime={currentTime}
            setCurrentTime={setCurrentTime}
            songData={songData}
            seekTo={(time) => handleSeekTo(time)}
            wsSend={wsSend}
            analysisResult={analysisResult}
            currentSongFile={currentSongFile}
          />
        )}


        {/* Fixtures Control */}
        <div>
          <Fixtures
            fixtures={fixtures}
            currentTime={currentTime}
            fixturesPresets={fixturesPresets}
            wsSend={wsSend}
          />
        </div>

      </div>
    </div>
  );
}
