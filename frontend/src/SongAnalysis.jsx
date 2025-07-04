import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";
import Bar from "./Bar";

export default function SongAnalysis({ songData, currentTime, setCurrentTime }) {

    const [beats, setBeats] = useState([]);
    const [currentBeat, setCurrentBeat] = useState(false);
    const [minEnergy, setMinEnergy] = useState(0);
    const [maxEnergy, setMaxEnergy] = useState(0);
    const currentBeatRef = useRef(null);

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
    }, [currentTime]);

    useEffect(() => {
      if (currentBeatRef.current) {
        currentBeatRef.current.scrollIntoView({
          behavior: 'smooth',
          inline: 'center',
          block: 'nearest'
        });
      }
    }, [currentBeat]);

    return (
    <>
      <h2 className="text-x2 font-bold mb-4">🤖 Song Analysis</h2>
      
      {/* Drum Parts */}
      <div className="mt-4">
        <h3 className="text-x1 font-bold mb-2">Drum Parts</h3>
        <div className="overflow-x-auto">
          <div className="px-1">
            {songData.drums && songData.drums.map((_type, index) => (
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

      {/* Song Beats */}
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

    </>
  );
}
