import { h } from 'preact';
import SongKeyMoments from './song/SongKeyMoments';
import LightingPlan from './song/LightingPlan';
import SongArrangement from './song/SongArrangement';
import ChordsCard from './song/ChordsCard';
import SongAnalysis from './song/SongAnalysis';

/**
 * SongMetadata component that groups together song metadata related components
 * including key moments, arrangement, and chord information
 */
export default function SongMetadata({ 
  currentTime, 
  setCurrentTime, 
  songData, 
  seekTo, 
  wsSend,
  analysisResult,
  currentSongFile
}) {
  const handleSeekTo = (time) => {
    if (seekTo) seekTo(time);
  };

  return (
    <>
      {/* Song Key Moments */}
      <div>
        <SongKeyMoments
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          songData={songData}
          seekTo={(time) => handleSeekTo(time)}
          saveKeyMoments={(km) => {wsSend("saveKeyMoments", {key_moments: km})}}
        />
      </div>

      {/* Song Arrangement */}
      <div>
        <SongArrangement
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          songData={songData}
          seekTo={(time) => handleSeekTo(time)}
          saveArrangement={(a) => {wsSend("saveArrangement", {arrangement: a})}}
        />
      </div>

      {/* Chords Information */}
      <div>
        <ChordsCard 
          songData={songData} 
          currentTime={currentTime} 
          setCurrentTime={setCurrentTime} 
        />
      </div>

      {/* Song Analysis */}
      <div>
        <SongAnalysis 
          songData={songData} 
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          analyzeSong={(data) => {
            // Use the same pattern as in the original App component
            const resetEvent = new CustomEvent('resetAnalysisResult');
            window.dispatchEvent(resetEvent);
            wsSend("analyzeSong", data);
          }}
          analysisResult={analysisResult}
          currentSongFile={currentSongFile}
        />
      </div>

    </>
  );
}
