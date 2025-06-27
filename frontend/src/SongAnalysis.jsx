import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";

export default function SongAnalysis({ analysisResult, currentTime, setCurrentTime }) {

    const [regions, setRegions] = useState([]);
    const [currentRegion, setCurrentRegion] = useState(false);
    const [minEnergy, setMinEnergy] = useState(0);
    const [maxEnergy, setMaxEnergy] = useState(0);
    const currentRegionRef = useRef(null);

    const [chords, setChords] = useState([]);
    const [currentChord, setCurrentChord] = useState(false);

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
      if (analysisResult.regions) {
        setRegions(analysisResult.regions);
        setChords(analysisResult.chords || []);
      }
    }, [analysisResult]);

    useEffect(() => {
      setMinEnergy(Math.min(...regions.map(region => region.energy)));
      setMaxEnergy(Math.max(...regions.map(region => region.energy)));
    }, [regions]);

    useEffect(() => {
        let current = null;
        for (let i = 0; i < regions.length; i++) {
          if (currentTime >= regions[i].start) current = i;
        }
        setCurrentRegion(current);
    }, [currentTime]);

    useEffect(() => {
      if (currentRegionRef.current) {
        currentRegionRef.current.scrollIntoView({
          behavior: 'smooth',
          inline: 'center',
          block: 'nearest'
        });
      }
    }, [currentRegion]);

    useEffect(() => {
        let current = null;
        for (let i = 0; i < chords.length; i++) {
          if (currentTime >= chords[i].aligned_time) current = i;
        }
        setCurrentChord(current);
    }, [currentTime]);

    return (
    <>
      <h2 className="text-2xl font-bold mb-4">Song Analysis</h2>
      <div>
        <p className="text-sm text-gray-300 mb-2">BPM: <span className="font-bold">{analysisResult.bpm}</span></p>
      </div>

      {/* Chords Section */}
      <div className="mt-4">
        <h3 className="text-xl font-bold mb-2">Chords</h3>
        <div className="overflow-x-auto">
          <div className="flex items-end space-x-1 px-1 py-2">
            {chords.map((chord, index) => (
              <div
                key={index}
                className={`flex flex-col items-center transition-all duration-200 ${
                    index === currentChord ? 'ring-2 ring-gray-400' : ''
                  }`}
                onClick={() => setCurrentTime(chord.aligned_time)}
              >
                {/* Chord Box */}
                <div
                  className="bg-blue-500 text-white text-xs rounded p-1 mb-1"
                  style={{ minWidth: '20px'}}
                >
                  {chord.chord}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      

      
      {/* Song Regions */}
      <div className="mt-4">
        <h3 className="text-xl font-bold mb-2">Regions</h3>
        <div className="overflow-x-auto">
          <div className="flex items-end space-x-1 px-1 py-2">
            {regions.map((region, index) => {
              const energyPercent = ((region.energy - minEnergy) / (maxEnergy - minEnergy)) * 100;

              return (
                <div
                  key={index}
                  ref={index === currentRegion ? currentRegionRef : null}
                  className={`flex flex-col items-center transition-all duration-200 ${
                    index === currentRegion ? 'ring-2 ring-gray-400' : ''
                  }`}
                  style={{ width: '20px' }}
                  onClick={()=>{setCurrentTime(region.start)}}
                >
                  {/* Energy Container */}
                  <div
                    className="flex items-end w-full bg-gray-800 rounded"
                    style={{ height: '100px' }}
                  >
                    <div
                      className="bg-green-500 w-full rounded-t"
                      style={{
                        height: `${energyPercent}%`,
                        transition: 'height 0.2s',
                      }}
                    ></div>
                  </div>

                  {/* Label Box */}
                  <div
                    className="w-full text-xs text-white flex items-center justify-center mt-1"
                    style={{
                      backgroundColor: labelColorMap[region.label],
                      height: '20px',
                      minWidth: '15px',
                    }}
                  >
                    {region.label}
                  </div>
                </div>
              );
            })}

          </div>
        </div>
      </div>

    </>
  );
}
