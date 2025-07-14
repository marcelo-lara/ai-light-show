// Fixture Card

// DEPRECATED: PresetSelector import removed - cue system deprecated
// import PresetSelector from "./PresetSelector";
import FixtureDmxChannels from "./FixtureDmxChannels";
import { useState, useEffect, useRef } from "preact/hooks";

export default function FixtureCard({ fixture, currentTime, allPresets, wsSend }) {
  const [values, setValues] = useState({ ...fixture.current_values });
  const { name, channels, presets } = fixture;
  const [expandedMap, setExpandedMap] = useState({});
  const expanded = expandedMap[fixture.id] || false;

  const toggleExpanded = (fixtureId) => {
    setExpandedMap((prev) => ({
      ...prev,
      [fixtureId]: !prev[fixtureId],
    }));
  };

  const previewColor =
    channels.red !== undefined && channels.green !== undefined && channels.blue !== undefined
      ? `rgb(${values.red}, ${values.green}, ${values.blue})`
      : '#000';
  const previewDim = channels.dim !== undefined ? values.dim : 255;

  const sendDMXUpdate = (channelMap) => {
    if (wsSend) {
      wsSend("setDmx", { values: channelMap });
    }
  };  

  return (
    <div>
      <div
        className="flex items-center justify-between mb-2 cursor-pointer"
        onClick={() => toggleExpanded(fixture.id)}
      >
        <div className="flex items-center gap-2">
          <h3 className="text-white font-normal">{name}</h3>
          <div
            className="w-6 h-6 rounded border border-white"
            style={{ backgroundColor: previewColor, opacity: previewDim / 255 }}
          ></div>
        </div>
        <div className="text-white">{expanded ? '' : '⌵'}</div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 text-sm text-gray-300">
          
          <div className="mb-2">
            {/* DEPRECATED: PresetSelector removed - cue system deprecated */}
            {/* <PresetSelector
              fixture={fixture}
              presets={allPresets}
              currentTime={currentTime}
              onAddCue={(cue) => {addCue(cue);}}
              previewDmx={(cue) => {previewDmx(cue);}}
            /> */}
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

          <FixtureDmxChannels
            channels={channels}
            values={values}
            setValues={setValues}
            sendDMXUpdate={sendDMXUpdate}
          />

        </div>
      )}
    </div>
  );
}
