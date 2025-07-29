import { formatTime } from "../utils";
import { useEffect, useState, useRef } from 'preact/hooks';

// Light plan item schema: { id, start, end, name, description }
// Light plan is an array of light plan item objects

export default function LightingPlan({
    currentTime,
    seekTo,
    lightPlan,
    setLightPlan,
    songData,
    saveLightPlan
}) {
    const [currentItem, setCurrentItem] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [showControls, setShowControls] = useState(false);
    const currentItemRef = useRef(null);

    // Find the current light plan item based on current time
    useEffect(() => {
        let currentIdx = null;
        for (let i = 0; i < lightPlan.length; i++) {
            const item = lightPlan[i];
            // If item has end time defined, check if current time is within the range
            if (item.end && item.end > item.start) {
                if (currentTime >= item.start && currentTime <= item.end) {
                    currentIdx = i;
                    break;
                }
            } else {
                // If no end time or end equals start, use proximity-based selection
                if (currentTime >= item.start) {
                    currentIdx = i;
                } else {
                    break;
                }
            }
        }
        setCurrentItem(currentIdx);
    }, [currentTime, lightPlan]);

    // Auto-scroll to current item when it changes
    useEffect(() => {
        if (currentItemRef.current) {
            currentItemRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }, [currentItem]);

    const onSaveLightPlan = () => {
        setEditMode(false);
        saveLightPlan(lightPlan);
    };

    const updateItem = (idx, field, value) => {
        setLightPlan(prev => prev.map((item, i) =>
            i === idx ? { ...item, [field]: value } : item
        ));
    };

    const deleteItem = (idx) => {
        setLightPlan(prev => prev.filter((_, i) => i !== idx));
    };

    const addItem = () => {
        // Find a unique item name and ID
        let itemId = Math.max(0, ...lightPlan.map(item => item.id || 0)) + 1;
        let idx = lightPlan.length + 1;
        let name = `Light ${idx}`;
        const existingNames = new Set(lightPlan.map(item => item.name));
        while (existingNames.has(name)) {
            idx++;
            name = `Light ${idx}`;
        }
        const start = parseFloat(currentTime.toFixed(3));
        setLightPlan(prev => ([
            ...prev,
            { 
                id: itemId,
                start, 
                end: null, 
                name, 
                description: `Lighting plan at ${formatTime(start)}` 
            }
        ]));
    };

    const onDeleteAll = () => {
        setLightPlan([]);
        setCurrentItem(null);
        setEditMode(false);
    };

    return (
        <>
            <h2 className="text-lg mb-2 font-semibold">Lighting Plan</h2>
            <ul className="space-y-1 max-h-36 overflow-y-auto">
                {lightPlan
                    .sort((a, b) => a.start - b.start)
                    .map((item, idx) => (
                        <li 
                            key={item.id || idx} 
                            ref={idx === currentItem ? currentItemRef : null}
                            className={idx === currentItem ? 'bg-purple-700 px-2 py-1 rounded text-sm' : 'text-gray-300 text-sm'}
                        >
                            {editMode ? (
                                <div className="flex items-center gap-2">
                                    <input 
                                        className="text-black px-1 rounded w-16" 
                                        type="number" 
                                        step="0.1"
                                        value={item.start} 
                                        onChange={e => updateItem(idx, 'start', parseFloat(e.target.value))} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-24" 
                                        value={item.name} 
                                        onChange={e => updateItem(idx, 'name', e.target.value)} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-40" 
                                        value={item.description || ''} 
                                        onChange={e => updateItem(idx, 'description', e.target.value)} 
                                    />
                                    <input 
                                        className="text-black px-1 rounded w-16" 
                                        type="number" 
                                        step="0.1"
                                        min="0"
                                        value={item.end || item.start} 
                                        onChange={e => updateItem(idx, 'end', parseFloat(e.target.value) || null)} 
                                        placeholder="End Time"
                                    />
                                    <button 
                                        onClick={() => deleteItem(idx)}
                                        className="text-red-500 hover:text-red-700 px-1"
                                        title="Delete lighting plan item"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ) : (
                                <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <span
                                            className="cursor-pointer hover:text-gray-500"
                                            onClick={() => seekTo(item.start)}
                                        >
                                            {formatTime(item.start)} - {item.name}{item.end && item.end > item.start ? ` (to ${formatTime(item.end)})` : ''}
                                        </span>
                                        
                                        <span className="text-gray-400 block"> 
                                            {item.description}
                                        </span>
                                    </div>
                                    <button 
                                        onClick={() => deleteItem(idx)}
                                        className="text-red-500 hover:text-red-700 px-2 py-1 text-xs opacity-70 hover:opacity-100"
                                        title="Delete lighting plan item"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            )}
                        </li>
                    ))}
            </ul>
            {showControls && (
                <div className="flex items-center gap-2 mt-2">
                    <button onClick={onSaveLightPlan} className="bg-green-700 hover:bg-green-800 px-2 py-1 rounded text-sm">💾 Save</button>
                    <button onClick={addItem} className="bg-indigo-600 hover:bg-indigo-700 px-2 py-1 rounded text-sm">➕ Add</button>
                    <button onClick={() => onDeleteAll()} className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-sm">❌ Delete All</button>
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
