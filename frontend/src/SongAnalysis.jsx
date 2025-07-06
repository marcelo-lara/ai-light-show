import { useState, useRef } from "preact/hooks";
import { use, useEffect } from "react";
import Bar from "./Bar";

export default function SongAnalysis({ songData, currentTime, setCurrentTime }) {

    const [beats, setBeats] = useState([]);
    const [clusters, setClusters] = useState([]);
    const [currentBeat, setCurrentBeat] = useState(false);
    const [currentClusterBeat, setCurrentClusterBeat] = useState(0);
    const [minEnergy, setMinEnergy] = useState(0);
    const [maxEnergy, setMaxEnergy] = useState(0);
    const currentBeatRef = useRef(null);
    const currentClusterBeatRef = useRef(null);

    const ClusterTag = ({ cluster, currentTime, setCurrentTime }) => (
        <div
            className={`px-2 py-1 rounded text-xs cursor-pointer ${
                currentTime >= cluster.start && currentTime <= cluster.end 
                    ? 'bg-green-500' 
                    : 'bg-gray-900'
            }`} 
            onClick={() => setCurrentTime(cluster.start)}
        >
            {cluster.cluster}
        </div>
    );

    const BeatTags = ({ _cluster, currentTime, setCurrentTime }) => (
        <div className="text-xs">
            <div className="flex flex-row space-x-1">

              {/* <div className="">
                  {_cluster.stem}
              </div> */}
              {_cluster.tags && _cluster.tags.map((c, cIndex) => (
                  <ClusterTag 
                      key={cIndex}
                      cluster={c} 
                      currentTime={currentTime} 
                      setCurrentTime={setCurrentTime} 
                  />
              ))}
            </div>
        </div>
    );

    const BeatBlock = ({ beat, index, currentTime, setCurrentTime, isCurrent, beatRef }) => {
        const _time = beat.time || -1;
        const clustersForBeat = getClustersForBeat(_time);

        return (
            <div 
                ref={beatRef}
                className={`bg-gray-800 px-2 ${isCurrent ? 'ring-2 ring-blue-400' : ''}`}
            >
                <div className="">
                    {clustersForBeat.map((_cluster, clusterIndex) => (
                        <BeatTags 
                            key={clusterIndex}
                            _cluster={_cluster}
                            currentTime={currentTime}
                            setCurrentTime={setCurrentTime}
                        />
                    ))}
                </div>
                <div className="text-xs text-right">{index}</div>
            </div>
        );
    };

    const ClustersTimeline = ({ beats, currentTime, setCurrentTime, currentClusterBeat, currentClusterBeatRef }) => (
        <div className="mt-4">
            <h3 className="text-x1 font-bold mb-2">clusters timeline</h3>
            <div className="overflow-x-auto flex flex-row space-x-1">
                {beats.map((beat, index) => (
                    <BeatBlock 
                        key={index}
                        beat={beat}
                        index={index}
                        currentTime={currentTime}
                        setCurrentTime={setCurrentTime}
                        beatRef={index === currentClusterBeat ? currentClusterBeatRef : null}
                        isCurrent={index === currentClusterBeat}
                    />
                ))}
            </div>
        </div>
    );

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
      if (songData.clusters) {
        setClusters(songData.clusters);
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
      }
    }, [currentClusterBeat]);

    function getClustersForBeat(beatTime) {
      const retval = [];
      for(const cluster of clusters){

        // get clusters where 'start' is in this beat time
        const filteredClusters = cluster.clusters.filter(c => {
          return c.start <= beatTime && c.end >= beatTime;
        });
        // add the cluster placeholder
        retval.push({
          stem: cluster.stem,
          tags: filteredClusters
        });
      }
      return retval;
    }

    function getUniqueClusters(clusters) {
      const uniqueClusterNumbers = [];
      for (const c of clusters) {
        if (uniqueClusterNumbers.includes(c.cluster)) continue;
        uniqueClusterNumbers.push(c.cluster);
      }
      // sort the cluster numbers
      uniqueClusterNumbers.sort((a, b) => a - b);
      console.log("uniqueClusterNumbers", uniqueClusterNumbers);
      return uniqueClusterNumbers
    }

    function getCurrentClusterNumber(currentTime, clusters) {
      for (const cluster of clusters) {
        for (const c of cluster.clusters) {
          if (c.start <= currentTime && c.end >= currentTime) {
            return c.cluster;
          }
        }
      }
      return null;
    }

    return (
    <>
      <h2 className="text-x2 font-bold mb-4">🤖 Song Analysis</h2>

        <div className="mt-4">
          <h3 className="text-x1 font-bold mb-2">clusters</h3>
          {/* unique clusters by stem */}
          <div className="overflow-x-auto">
            { clusters.map((cluster, index) => (
              <div key={index} className="px-1 py-2">
                <div className="flex items-center space-x-1">
                  <div className="text-xs">{cluster.stem}</div>
                  {getUniqueClusters(cluster.clusters).map((c, cIndex) => (
                    <div
                      className="rounded text-xs"
                      key={cIndex}
                    >
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )) }  
          </div>
        </div>      



      {/* Beats and clusters */}
      {clusters.length > 0 && (
        <ClustersTimeline 
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
