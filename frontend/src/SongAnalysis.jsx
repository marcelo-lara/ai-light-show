
import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";

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

  function BarLevel({ level }) {
    return (
      <div
        className="flex items-end w-full bg-gray-800 rounded"
        style={{ height: '100px' }}
      >
        <div
          className="bg-green-500 w-full rounded-t"
          style={{
            height: `${level}%`,
            transition: 'height 0.2s',
          }}
        ></div>
      </div>
    );
  }

  function BarLabel({ label, color }) {
    return (
      <div
        className="w-full text-xs text-white flex items-center justify-center mt-1"
        style={{
          backgroundColor: color || 'gray',
          height: '20px',
          minWidth: '15px',
        }}
      >
        {label}
      </div>
    );
  }
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
                  className={`flex flex-col items-center transition-all duration-200 ${
                    index === currentBeat ? 'ring-2 ring-gray-400' : ''
                  }`}
                  style={{ width: '20px' }}
                  onClick={()=>{setCurrentTime(beat.time)}}
                >
                  {/* Energy Container */}
                  <BarLevel level={energyPercent} />

                  {/* Label Box */}
                  <BarLabel 
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
