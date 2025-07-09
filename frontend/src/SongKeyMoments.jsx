import { formatTime } from "./utils";
import { useEffect, useState, useRef } from 'preact/hooks';

// Key moment schema: { time, name, description, duration }
// Key moments is an array of key moment objects

export default function SongKeyMoments({
    currentTime,
    seekTo,
    setCurrentTime,
    songData,
    saveKeyMoments
}) {
    const [currentMoment, setCurrentMoment] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [keyMoments, setKeyMoments] = useState([]);
    const [showControls, setShowControls] = useState(false);
    const currentMomentRef = useRef(null);

    // Load key moments from song data if available
    useEffect(() => {
        setKeyMoments(Array.isArray(songData?.key_moments) ? songData.key_moments : []);
    }, [songData]);

    // Find the current key moment based on current time
    useEffect(() => {
        let currentIdx = null;
        for (let i = 0; i < keyMoments.length; i++) {
            const moment = keyMoments[i];
            // If moment has duration > 0, check if current time is within the duration
            if (moment.duration && moment.duration > 0) {
                if (currentTime >= moment.time && currentTime <= moment.time + moment.duration) {
                    currentIdx = i;
                    break;
                }
            } else {
                // If no duration or duration is 0, use proximity-based selection
                if (currentTime >= moment.time) {
                    currentIdx = i;
                } else {
                    break;
                }
            }
        }
        setCurrentMoment(currentIdx);
    }, [currentTime, keyMoments]);

    // Auto-scroll to current moment when it changes
    useEffect(() => {
        if (currentMomentRef.current) {
            currentMomentRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }, [currentMoment]);

    const onSaveKeyMoments = () => {
        setEditMode(false);
        saveKeyMoments(keyMoments);
    };

    const updateMoment = (idx, field, value) => {
        setKeyMoments(prev => prev.map((moment, i) =>
            i === idx ? { ...moment, [field]: value } : moment
        ));
    };

    const deleteMoment = (idx) => {
        setKeyMoments(prev => prev.filter((_, i) => i !== idx));
    };

    const addMoment = () => {
        // Find a unique moment name
        let idx = keyMoments.length + 1;
        let name = `Moment ${idx}`;
        const existingNames = new Set(keyMoments.map(m => m.name));
        while (existingNames.has(name)) {
            idx++;
            name = `Moment ${idx}`;
        }
        const time = parseFloat(currentTime.toFixed(3));
        setKeyMoments(prev => ([
            ...prev,
            { time, name, description: `Key moment at ${formatTime(time)}`, duration: 0 }
        ]));
    };

    return (
        <>
            <h2 className="text-lg mb-2 font-semibold">Key Moments</h2>
            <ul className="space-y-1 max-h-36 overflow-y-auto">
                {keyMoments
                    .sort((a, b) => a.time - b.time)
                    .map((moment, idx) => (
                        <li 
                            key={idx} 
                            ref={idx === currentMoment ? currentMomentRef : null}
                            className={idx === currentMoment ? 'bg-blue-700 px-2 py-1 rounded text-sm' : 'text-gray-300 text-sm'}
                        >
                            {editMode ? (
                                <div className="flex items-center gap-2">
                                    <input 
                                        className="text-black px-1 rounded w-16" 
                                        type="number" 
                                        step="0.1"
                                        value={moment.time} 
                                        onChange={e => updateMoment(idx, 'time', parseFloat(e.target.value))} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-24" 
                                        value={moment.name} 
                                        onChange={e => updateMoment(idx, 'name', e.target.value)} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-40" 
                                        value={moment.description} 
                                        onChange={e => updateMoment(idx, 'description', e.target.value)} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-16" 
                                        type="number" 
                                        step="0.1"
                                        min="0"
                                        value={moment.duration || 0} 
                                        onChange={e => updateMoment(idx, 'duration', parseFloat(e.target.value) || 0)} 
                                        placeholder="Duration"
                                    />
                                    <button onClick={() => deleteMoment(idx)}>❌</button>
                                </div>
                            ) : (
                                <>
                                    <span
                                        className="cursor-pointer hover:text-gray-500"
                                        onClick={() => seekTo(moment.time)}
                                    >
                                        {formatTime(moment.time)} - {moment.name}{moment.duration > 0 ? ` (${moment.duration}s)` : ''}
                                    </span>
                                    
                                    <span className="text-gray-400" style="display: block"> 
                                        {moment.description}
                                    </span>
                                </>
                            )}
                        </li>
                    ))}
            </ul>
            {showControls && (
                <div className="flex items-center gap-2 mt-2">
                    <button onClick={onSaveKeyMoments} className="bg-green-700 hover:bg-green-800 px-2 py-1 rounded text-sm">💾 Save</button>
                    <button onClick={addMoment} className="bg-indigo-600 hover:bg-indigo-700 px-2 py-1 rounded text-sm">➕ Add</button>
                    <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-2 py-1 rounded text-sm">✏️ {editMode ? 'Exit' : 'Edit'}</button>
                    <button onClick={() => setShowControls(!showControls)} className="bg-gray-600 hover:bg-gray-700 px-2 py-1 rounded text-sm">⚙️</button>
                </div>
            )}
            {!showControls && (
                <button onClick={() => setShowControls(true)} className="bg-gray-600 hover:bg-gray-700 px-2 py-1 rounded text-sm mt-2">⚙️</button>
            )}
        </>
    );
}
