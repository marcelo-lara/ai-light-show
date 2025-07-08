import { formatTime } from "./utils";
import { useEffect, useState, useRef } from 'preact/hooks';

// Section schema: { name, start, end, prompt }
// Arrangement is an array of Sections


export default function SongArrangement({
    currentTime,
    seekTo,
    setCurrentTime,
    songData,
    saveArrangement
}) {
    const [currentSection, setCurrentSection] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [arrangement, setArrangement] = useState([]);
    const [showControls, setShowControls] = useState(false);
    const currentSectionRef = useRef(null);

    // Load arrangement from song data if available
    useEffect(() => {
        setArrangement(Array.isArray(songData?.arrangement) ? songData.arrangement : []);
    }, [songData]);

    // Find the current section based on current time
    useEffect(() => {
        let currentIdx = null;
        for (let i = 0; i < arrangement.length; i++) {
            const section = arrangement[i];
            if (currentTime >= section.start && currentTime < section.end) {
                currentIdx = i;
                break;
            }
        }
        setCurrentSection(currentIdx);
    }, [currentTime, arrangement]);

    // Auto-scroll to current section when it changes
    useEffect(() => {
        if (currentSectionRef.current) {
            currentSectionRef.current.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }, [currentSection]);

    const onSaveArrangement = () => {
        setEditMode(false);
        saveArrangement(arrangement);
    };

    const updateSection = (idx, field, value) => {
        setArrangement(prev => prev.map((section, i) =>
            i === idx ? { ...section, [field]: value } : section
        ));
    };

    const deleteSection = (idx) => {
        setArrangement(prev => prev.filter((_, i) => i !== idx));
    };

    const addSection = () => {
        // Find a unique section name
        let idx = arrangement.length + 1;
        let name = `section_${idx}`;
        const existingNames = new Set(arrangement.map(s => s.name));
        while (existingNames.has(name)) {
            idx++;
            name = `section_${idx}`;
        }
        const start = parseFloat(currentTime.toFixed(3));
        const end = start + 5; // default 5s section
        setArrangement(prev => ([
            ...prev,
            { name, start, end, prompt: `Section ${idx}` }
        ]));
    };

    return (
    <>
        <h2 className="text-lg mb-2 font-semibold">Arrangement</h2>
        <ul className="space-y-1 max-h-36 overflow-y-auto">
            {arrangement.map((section, idx) => (
                <li 
                    key={idx} 
                    ref={idx === currentSection ? currentSectionRef : null}
                    className={idx === currentSection ? 'bg-green-700 px-2 py-1 rounded text-sm' : 'text-gray-300 text-sm'}
                >
                    {editMode ? (
                        <div className="flex items-center gap-2">
                            <input className="text-black px-1 rounded w-28" value={section.name} readOnly />
                            <input className="text-black px-1 rounded w-64" value={section.prompt} onChange={e => updateSection(idx, 'prompt', e.target.value)} />
                            <button onClick={() => deleteSection(idx)}>❌</button>
                        </div>
                    ) : (
                        <>
                            <span
                                className="cursor-pointer hover:text-gray-500"
                                onClick={() => seekTo(section.start)}
                            >
                                {section.name}
                            </span>
                            
                            <span className="text-gray-400" style="display: block"> 
                                {section.prompt}
                            </span>
                        </>
                    )}
                </li>
            ))}
        </ul>
        {showControls && (
            <div className="flex items-center gap-4 mb-4">
                <button onClick={onSaveArrangement} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save</button>
                <button onClick={addSection} className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">➕ Add Section</button>
                <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">✏️ {editMode ? 'Exit Edit Mode' : 'Edit'}</button>
            </div>
        )}
    </>
    );
}
