import { formatTime } from "./utils";
import { useEffect, useState } from 'preact/hooks';

// Section schema: { start, end, prompt }
// Arrangement schema: { [sectionName]: Section }

export default function SongArrangement({
    currentTime,
    songData,
    saveArrangement
}) {
    const [currentSection, setCurrentSection] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [arrangement, setArrangement] = useState({});

    // Load arrangement from song data if available
    useEffect(() => {
        setArrangement(songData?.arrangement || {});
    }, [songData]);

    // Find the current section based on current time
    useEffect(() => {
        let current = null;
        for (const [name, section] of Object.entries(arrangement)) {
            if (currentTime >= section.start && currentTime < section.end) {
                current = name;
                break;
            }
        }
        setCurrentSection(current);
    }, [currentTime, arrangement]);

    const onSaveArrangement = () => {
        setEditMode(false);
        saveArrangement(arrangement);
    };

    const updateSection = (name, field, value) => {
        setArrangement(prev => ({
            ...prev,
            [name]: {
                ...prev[name],
                [field]: value
            }
        }));
    };

    const deleteSection = (name) => {
        const updated = { ...arrangement };
        delete updated[name];
        setArrangement(updated);
    };

    const addSection = () => {
        // Find a unique section name
        let idx = Object.keys(arrangement).length + 1;
        let name = `section_${idx}`;
        while (arrangement[name]) {
            idx++;
            name = `section_${idx}`;
        }
        const start = parseFloat(currentTime.toFixed(3));
        const end = start + 5; // default 5s section
        setArrangement({
            ...arrangement,
            [name]: {
                start,
                end,
                prompt: `Section ${idx}`
            }
        });
    };

    return (
        <>
            <div className="flex items-center gap-4 mb-4">
                <button onClick={onSaveArrangement} className="bg-green-700 hover:bg-green-800 px-4 py-2 rounded">💾 Save</button>
                <button onClick={addSection} className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded">➕ Add Section</button>
                <button onClick={() => setEditMode(!editMode)} className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded">✏️ {editMode ? 'Exit Edit Mode' : 'Edit'}</button>
            </div>

            <div className="bg-white/10 rounded p-4 text-sm">
                <h2 className="text-lg mb-2 font-semibold">Arrangement</h2>
                <ul className="space-y-1">
                    {Object.entries(arrangement).map(([name, section]) => (
                        <li key={name} className={name === currentSection ? 'bg-green-700 px-2 py-1 rounded' : 'text-gray-300'}>
                            {editMode ? (
                                <div className="flex items-center gap-2">
                                    <input className="text-black px-1 rounded w-28" value={name} readOnly />
                                    <input className="text-black px-1 rounded w-16" type="number" step="0.01" value={section.start} onChange={e => updateSection(name, 'start', parseFloat(e.target.value))} />
                                    <input className="text-black px-1 rounded w-16" type="number" step="0.01" value={section.end} onChange={e => updateSection(name, 'end', parseFloat(e.target.value))} />
                                    <input className="text-black px-1 rounded w-64" value={section.prompt} onChange={e => updateSection(name, 'prompt', e.target.value)} />
                                    <button onClick={() => deleteSection(name)}>❌</button>
                                </div>
                            ) : (
                                <>
                                    <span className="font-bold">{name}</span> {section.prompt}
                                </>
                            )}
                        </li>
                    ))}
                </ul>
            </div>
        </>
    );
}
