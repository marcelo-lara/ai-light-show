import { formatTime, saveToServer, SongsFolder } from "./utils";
import { useEffect, useRef, useState } from 'preact/hooks';

export default function SongArrangement({
    currentTime,
    songData,
    saveArrangement
}) {

    const [currentSection, setCurrentSection] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [arrangement, setArrangement] = useState([]);    

    // Load arrangement from song data if available
    useEffect(() => {
            setArrangement(songData?.arrangement || []);
    }, [songData]);

    // Set the current section based on current time
    useEffect(() => {
        let current = null;
        for (let i = 0; i < arrangement.length; i++) {
        if (currentTime >= arrangement[i].time) current = i;
        }
        setCurrentSection(current);
    }, [currentTime]);

    const onSaveArrangement = () => {
        setEditMode(false);
        saveArrangement(arrangement)
    };

    const updateMarker = (index, label) => {
        const updated = [...arrangement];
        updated[index].label = label;
        setArrangement(updated);
    };

    const deleteMarker = (index) => {
        const updated = [...arrangement];
        updated.splice(index, 1);
        setArrangement(updated);
    };

    const addMarker = () => {
        const time = parseFloat(currentTime.toFixed(3));
        const newMarker = { time, label: `Section ${arrangement.length + 1}` };
        setArrangement([...arrangement, newMarker]);
    };

    return (
        <>
            <div className="flex items-center gap-4 mb-4">
                <button onClick={onSaveArrangement} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save</button>
                <button onClick={addMarker} className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">➕ Add Marker</button>
                <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">✏️ {editMode ? 'Exit Edit Mode' : 'Edit'}</button>
            </div>

            <div className="bg-white/10 rounded p-4 text-sm">
                <h2 className="text-lg mb-2 font-semibold">Arrangement</h2>
                <ul className="space-y-1">
                    {arrangement.map((section, index) => (
                        <li key={index} className={index === currentSection ? 'bg-green-700 px-2 py-1 rounded' : 'text-gray-300'}>
                            {editMode ? (
                                <div className="flex items-center gap-2">
                                    <input className="text-black px-1 rounded" value={section.label} onChange={(e) => updateMarker(index, e.target.value)} />
                                    <button onClick={() => deleteMarker(index)}>❌</button>
                                </div>
                            ) : (
                                <>[{formatTime(section.time)}] {section.label}</>
                            )}
                        </li>
                    ))}
                </ul>
            </div>
        </>
    );
}
