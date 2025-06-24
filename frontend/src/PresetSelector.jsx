// PresetSelector.jsx

import { useState } from "preact/hooks";

export default function PresetSelector({ fixture, presets, currentTime, onAddCue }) {
  const [selected, setSelected] = useState(null);
  const [paramValues, setParamValues] = useState({});

  const applicablePresets = presets.filter(p => p.type === fixture.type);

  const handleSelect = (preset) => {
    setSelected(preset);
    setParamValues(preset.parameters || {});
  };

  const handleParamChange = (key, value) => {
    setParamValues(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="text-sm text-white p-2">
      <h3 className="font-semibold mb-2">Presets for {fixture.name}</h3>
      <ul className="mb-4 flex flex-row flex-wrap gap-2">
        {applicablePresets.map(p => (
          <li key={p.name}>
            <button
              className="text-blue-400 underline"
              onClick={() => handleSelect(p)}
            >
              {p.name}
            </button>
          </li>
        ))}
      </ul>
      {selected && (
        <div className="border border-white/10 rounded">
          <h4 className="font-semibold mb-1">Parameters</h4>
          <div className="flex flex-col gap-2 mb-2">
            {Object.entries(selected.parameters || {}).map(([key, defaultVal]) => (
              <label key={key} className="flex flex-col">
                <span className="text-gray-300">{key}</span>
                <input
                  type="number"
                  className="bg-gray-800 p-1 rounded text-white"
                  value={paramValues[key]}
                  onChange={(e) => handleParamChange(key, parseInt(e.target.value))}
                />
              </label>
            ))}
          </div>
          <button
            onClick={() =>
              onAddCue({
                time: parseFloat(currentTime.toFixed(2)),
                fixture: fixture.id,
                preset: selected.name,
                parameters: { ...paramValues }
              })
            }
            className="bg-green-700 text-white px-3 py-1 rounded hover:bg-green-600"
          >
            + Add to Cue @{currentTime.toFixed(3)}s
          </button>          
        </div>
      )}
    </div>
  );
}