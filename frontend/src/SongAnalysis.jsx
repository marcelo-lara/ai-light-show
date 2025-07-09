import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";
import Bar from "./Bar";
import PatternsTimeline from "./PatternsTimeline";

export default function SongAnalysis({ songData, currentTime, setCurrentTime, analyzeSong, analysisResult, currentSongFile }) {

    const [beats, setBeats] = useState([]);
    const [patterns, setPatterns] = useState([]);
    const [currentBeat, setCurrentBeat] = useState(false);
    const [currentClusterBeat, setCurrentClusterBeat] = useState(0);
    const [minEnergy, setMinEnergy] = useState(0);
    const [maxEnergy, setMaxEnergy] = useState(0);
    const [showPatterns, setShowPatterns] = useState(true);
    const [showPatternsTimeline, setShowPatternsTimeline] = useState(false);
    const [showBeats, setShowBeats] = useState(false);
    const [generateCues, setGenerateCues] = useState(false);
    const currentBeatRef = useRef(null);
    const currentClusterBeatRef = useRef(null);

    const labelColorMap = {
        'A': '#1d4ed8', // Blue
        'B': '#10b981', // Green
        'C': '#ef4444', // Red
        'D': '#8b5cf6', // Purple
        'E': '#f472b6', // Pink
        'F': '#f97316', // Orange
        'G': '#f59e0b', // Yellow
        'H': '#0ea5e9'  // Sky Blue
    };

    useEffect(() => {
      if (songData.beats) {
        setBeats(songData.beats);
      }
      if (songData.patterns) {
        setPatterns(songData.patterns);
      }
    }, [songData]);

    useEffect(() => {
      setMinEnergy(Math.min(...beats.map(region => region.volume)));
      setMaxEnergy(Math.max(...beats.map(region => region.volume)));
    }, [beats]);

    useEffect(() => {
        let current = 0;
        for (let i = 0; i < beats.length; i++) {
          if (currentTime >= beats[i].time) current = i;
        }
        setCurrentBeat(current);
        setCurrentClusterBeat(current);
    }, [currentTime, beats]);

    useEffect(() => {
      if (currentBeatRef.current) {
        currentBeatRef.current.scrollIntoView({
          behavior: 'smooth',
          inline: 'center',
          block: 'nearest'
        });
      }
    }, [currentBeat]);

    useEffect(() => {
      if (currentClusterBeatRef.current) {
        currentClusterBeatRef.current.scrollIntoView({
          behavior: 'smooth',
          inline: 'center',
          block: 'nearest'
        });
      }      }, [currentClusterBeat]);

    function getUniquePatterns(patterns) {
      const uniquePatternNumbers = [];
      for (const c of patterns) {
        if (uniquePatternNumbers.includes(c.cluster)) continue;
        uniquePatternNumbers.push(c.cluster);
      }
      // sort the cluster numbers
      uniquePatternNumbers.sort((a, b) => a - b);
      return uniquePatternNumbers
    }

    function getCurrentPatternNumber(currentTime, patterns) {
      for (const pattern of patterns) {
        for (const c of pattern.clusters) {
          if (c.start <= currentTime && c.end >= currentTime) {
            return c.cluster;
          }
        }
      }
      return null;
    }

    const handleAnalyzeSong = () => {
      analyzeSong({songFile: currentSongFile, renderTestCues: generateCues});
    }

    return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-x2 font-bold">🤖 Song Analysis</h2>
        <div>
          <div className="flex items-center space-x-6">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showPatterns}
                onChange={(e) => setShowPatterns(e.target.checked)}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm">Patterns</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showPatternsTimeline}
                onChange={(e) => setShowPatternsTimeline(e.target.checked)}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm">Patterns Timeline</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showBeats}
                onChange={(e) => setShowBeats(e.target.checked)}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm">Beats</span>
            </label>

            {/* Analysis controls */}
            <button 
              onClick={() => handleAnalyzeSong()} 
              className={`px-3 py-1 rounded text-sm ${!currentSongFile ? 'bg-gray-900 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`} 
              disabled={!currentSongFile}
            >
              🔍 Analyze Song
            </button>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={generateCues}
                onChange={e => setGenerateCues(e.target.checked)}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm">Generate Cues</span>
            </label>

          </div>
        </div>
      </div>

        {showPatterns && (
        <div className="mt-4">
          <h3 className="text-x1 font-bold mb-2">patterns</h3>
          {/* unique clusters by stem */}
          <div className="overflow-x-auto">
            { patterns.map((pattern, index) => (
              <div key={index} className="px-1 py-2">
                <div className="text-xs">{pattern.stem}</div>
                <div className="flex space-x-3">
                  {getUniquePatterns(pattern.clusters).map((cluster, cIndex) => {
                    // Check if this cluster is currently active
                    const isCurrentCluster = pattern.clusters.some(c => 
                      c.cluster === cluster && 
                      currentTime >= c.start && 
                      currentTime <= c.end
                    );
                    
                    return (
                      <div
                        className={`rounded text-xs min-w-2 px-2 py-1 ${
                          isCurrentCluster 
                            ? 'bg-green-500 text-white' 
                            : 'bg-gray-700 text-gray-300'
                        }`}
                        key={cIndex}
                      >
                        {cluster}
                      </div>
                    );
                  })}
                </div>
              </div>
            )) }  
          </div>
        </div>
        )}      



      {/* Beats and patterns */}
      {showPatternsTimeline && patterns.length > 0 && (
        <PatternsTimeline 
          songData={songData}
          beats={beats}
          currentTime={currentTime}
          setCurrentTime={setCurrentTime}
          currentClusterBeat={currentClusterBeat}
          currentClusterBeatRef={currentClusterBeatRef}
        />
      )}

      {/* Drum Parts */}
      {songData.drums?.length>0 && (
        <div className="mt-4">
          <h3 className="text-x1 font-bold mb-2">Drum Parts</h3>
          <div className="overflow-x-auto">
            <div className="px-1">
              {songData.drums.map((_type, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="text-xs text-gray-400">{_type['type']}</div>
                  <div className="flex space-x-1">
                    {_type['time'].map((_time, regionIndex) => (
                      <div key={regionIndex} 
                          className={`px-2 py-1 rounded text-xs ${currentTime >= _time[0] ? 'bg-green-500' : 'bg-gray-900'}`} 
                          onClick={() => setCurrentTime(_time[0])}>
                        {_time[0]}<br />
                        {_time[1].toFixed(2)}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Song Beats */}
      {showBeats && (
      <div className="mt-4">
        <h3 className="text-x1 font-bold mb-2">beats</h3>
        <div className="overflow-x-auto">
          <div className="flex items-end space-x-1 px-1 py-2">
            {beats.map((beat, index) => {
              const energyPercent = ((beat.volume - minEnergy) / (maxEnergy - minEnergy)) * 100;

              return (
                <div
                  key={index}
                  ref={index === currentBeat ? currentBeatRef : null}
                  className={index === currentBeat ? 'ring-2 ring-gray-400' : ''}
                  onClick={() => setCurrentTime(beat.time)}
                >
                  <Bar
                    level={energyPercent}
                    label={index}
                    color={labelColorMap[beat.label]}
                  />
                </div>
              );
            })}

          </div>
        </div>
      </div>
      )}

    </>
  );
}
