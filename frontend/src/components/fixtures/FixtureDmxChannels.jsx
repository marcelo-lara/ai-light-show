import { useEffect, useRef } from "preact/hooks";

export default function FixtureDmxChannels({ channels, values, setValues, sendDMXUpdate }) {
  const handleValueChange = (key, dmx, val) => {
    const n = parseInt(val, 10);
    if (!isNaN(n) && n >= 0 && n <= 255) {
      setValues((prev) => ({ ...prev, [key]: n }));
    }
  };
  
  return (
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
  );
}
