// Fixture Card

import PresetSelector from "./PresetSelector";
import { useState, useEffect, useRef } from "preact/hooks";

export default function FixtureCard({ fixture, currentTime, addCue, sendDMXUpdate }) {
  const [values, setValues] = useState({ ...fixture.current_values });
  const { name, channels, presets } = fixture;
  const [expandedMap, setExpandedMap] = useState({});
  const expanded = expandedMap[fixture.id] || false;

  const [allPresets, setAllPresets] = useState([]);

  const toggleExpanded = (fixtureId) => {
    setExpandedMap((prev) => ({
      ...prev,
      [fixtureId]: !prev[fixtureId],
    }));
  };

  useEffect(() => {
    fetch("/fixtures/fixture_presets.json")
      .then((res) => res.json())
      .then((data) => setAllPresets(data))
      .catch((err) => console.error("Failed to load presets:", err));
  }, []);

  const previewColor =
    channels.red !== undefined && channels.green !== undefined && channels.blue !== undefined
      ? `rgb(${values.red}, ${values.green}, ${values.blue})`
      : '#000';
  const previewDim = channels.dim !== undefined ? values.dim : 255;

  const handleValueChange = (key, dmx, val) => {
    const n = parseInt(val, 10);
    if (!isNaN(n) && n >= 0 && n <= 255) {
      setValues((prev) => ({ ...prev, [key]: n }));
    }
  };

  return (
    <div className="border border-white/10 rounded-lg mb-4 bg-white/5 shadow-sm">
      <div
        className="flex items-center justify-between p-3 cursor-pointer"
        onClick={() => toggleExpanded(fixture.id)}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-6 h-6 rounded border border-white"
            style={{ backgroundColor: previewColor, opacity: previewDim / 255 }}
          ></div>
          <div className="font-semibold text-white">{name}</div>
        </div>
        <div className="text-white">{expanded ? '🔽' : '▶️'}</div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 text-sm text-gray-300">
          <div className="mb-2">
            <table className="text-xs w-full border-collapse">
              <thead>
                <tr className="text-gray-400">
                  <th className="text-left py-1">Channel</th>
                  <th className="text-left py-1">DMX</th>
                  <th className="text-left py-1">Value</th>
                </tr>
              </thead>
              <tbody>
              {Object.entries(channels).map(([key, dmx], idx) => {
                const val = values[key] ?? 0;
                const sliderRef = useRef(null);

                useEffect(() => {
                  const el = sliderRef.current;
                  if (!el) return;

                  const handleInput = (e) => {
                    const newVal = parseInt(e.target.value);
                    handleValueChange(key, dmx, newVal);
                    sendDMXUpdate({ [dmx]: newVal });
                  };

                  el.addEventListener("input", handleInput);
                  return () => el.removeEventListener("input", handleInput);
                }, [key, dmx]);                  
                return (
                  <tr key={idx} className="border-t border-white/10">
                    <td className="py-1">{key}</td>
                    <td className="py-1">{dmx}</td>
                    <td className="py-1">
                      <div className="flex items-center gap-2">
                        <input
                          ref={sliderRef}
                          type="range"
                          min={0}
                          max={255}
                          value={val}
                          className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />
                        <span className="w-8 text-xs text-right text-gray-300">{val}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>

          <div className="mb-2">
            <PresetSelector
              fixture={fixture}
              presets={allPresets}
              onApply={(preset, params) => {
                // send to backend or trigger execution
                console.log("Apply preset", preset.name, "with", params);
              }}
              currentTime={currentTime}
              onAddCue={(cue) => {
                addCue(cue);
              }}                
            />
          </div>
            

          {presets.length > 0 && (
            <div className="flex gap-2 flex-wrap mt-2">
              {presets.map((p, i) => (
                <button
                  key={i}
                  className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs"
                >
                  {p.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
