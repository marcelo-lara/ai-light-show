import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";

export default function SongAnalysis({ analysisResult, currentTime }) {

    const [regions, setRegions] = useState([]);
    const [currentRegion, setCurrentRegion] = useState(false);
    const [minEnergy, setMinEnergy] = useState(0);
    const [maxEnergy, setMaxEnergy] = useState(0);
    const currentRegionRef = useRef(null);

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
            const container = currentRegionRef.current.closest('.overflow-x-auto');
            if (container) {
                const containerRect = container.getBoundingClientRect();
                const regionRect = currentRegionRef.current.getBoundingClientRect();
                if (regionRect.top < containerRect.top || regionRect.bottom > containerRect.bottom) {
                    currentRegionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }
        }
    }, [currentRegion]);

  return (
    <>
      <h2 className="text-2xl font-bold mb-4">Song Analysis</h2>
      <div>
        <p className="text-sm text-gray-300 mb-2">BPM: <span className="font-bold">{analysisResult.bpm}</span></p>
      </div>
      
      {/* Song Regions */}
      <div className="mt-4">
        <h3 className="text-xl font-bold mb-2">Regions</h3>
        <div className="overflow-x-auto" style={{ maxHeight: 'calc(10 * 2.5rem)', overflowY: 'auto' }}>
          <table className="w-full text-sm text-gray-300">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left">Label</th>
                <th className="text-left">Start</th>
                <th className="text-left">Energy</th>
              </tr>
            </thead>
            <tbody>
              {regions.map((region, index) => (
                <tr
                  key={index}
                  ref={index === currentRegion ? currentRegionRef : null}
                  className={`border-b border-gray-700 ${index === currentRegion ? 'bg-green-800' : ''}`}
                >
                  <td className="w-3">
                    <div className="w-8 h-8 flex items-center justify-center rounded text-white" style={{ backgroundColor: labelColorMap[region.label]}}>
                      {region.label}
                    </div>
                  </td>
                  <td>{region.start.toFixed(2)}s</td>
                  <td>
                    <div className="w-full h-4 bg-gray-700 rounded">
                      <div
                        className="h-4 bg-green-500 rounded"
                        style={{ width: `${((region.energy - minEnergy) / (maxEnergy - minEnergy)) * 100}%` }}
                      ></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
