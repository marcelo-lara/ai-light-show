// Fixture Card

import FixtureDmxChannels from "./FixtureDmxChannels";
import FixtureActions from "./FixtureActions";
import { useState, useEffect, useRef } from "preact/hooks";

export default function FixtureCard({ fixture, currentTime, wsSend }) {
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
          
          <FixtureActions 
            fixture={fixture}
            currentTime={currentTime}
            wsSend={wsSend}
          />

          <FixtureDmxChannels
            channels={channels}
            setValues={setValues}
            sendDMXUpdate={sendDMXUpdate}
          />

        </div>
      )}
    </div>
  );
}
