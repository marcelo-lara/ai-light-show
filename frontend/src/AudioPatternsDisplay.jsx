import { useState } from "preact/hooks";

export default function AudioPatternsDisplay({ songData, beats, currentTime, setCurrentTime, currentClusterBeat, currentClusterBeatRef }) {
    const [patterns, setPatterns] = useState(songData.patterns || []);

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

    const BeatTags = ({ _pattern, currentTime, setCurrentTime }) => (
        <div className="text-xs">
            <div className="flex flex-row space-x-1">
                {_pattern.tags && _pattern.tags.map((c, cIndex) => (
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
        const patternsForBeat = getPatternsForBeat(_time);

        return (
            <div 
                ref={beatRef}
                className={`bg-gray-800 px-2 ${isCurrent ? 'ring-2 ring-blue-400' : ''}`}
            >
                <div className="">
                    {patternsForBeat.map((_pattern, patternIndex) => (
                        <BeatTags 
                            key={patternIndex}
                            _pattern={_pattern}
                            currentTime={currentTime}
                            setCurrentTime={setCurrentTime}
                        />
                    ))}
                </div>
                <div className="text-xs text-right">{index}</div>
            </div>
        );
    };

    function getPatternsForBeat(beatTime) {
        const retval = [];
        for(const pattern of patterns){
            // get patterns where 'start' is in this beat time
            const filteredPatterns = pattern.clusters.filter(c => {
                return c.start <= beatTime && c.end >= beatTime;
            });
            // add the pattern placeholder
            retval.push({
                stem: pattern.stem,
                tags: filteredPatterns
            });
        }
        return retval;
    }

    return (
        <div className="mt-4">
            <h3 className="text-x1 font-bold mb-2">audio patterns</h3>
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
}
