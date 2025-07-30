import { useEffect, useRef, useState } from "preact/hooks";
import { useWebSocket } from '../../context/WebSocketContext.jsx';

export default function FixtureDmxChannels({ channels, sendDMXUpdate }) {
  const [values, setValues] = useState({});
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    // Initialize values from channels data
    const initialValues = {};
    channels.forEach(channel => {
      initialValues[channel.ch] = channel.value;
    });
    setValues(initialValues);
  }, [channels]);

  const handleValueChange = (ch, val) => {
    const n = parseInt(val, 10);
    if (!isNaN(n) && n >= 0 && n <= 255) {
      setValues((prev) => ({ ...prev, [ch]: n }));
      sendDMXUpdate({ [ch]: n });
    }
  };
  
useEffect(() => {
    // Log the channels for debugging
    console.log("lastMessage from FixtureDmxChannels:", lastMessage);
  }, [lastMessage]);

  console.log("FixtureDmxChannels", { channels });

  return (
    <table className="text-xs w-full border-collapse">
      <thead>
        <tr className="text-gray-400">
          <th className="text-left py-1">Channel</th>
          <th className="text-left py-1">Name</th>
          <th className="text-left py-1">Value</th>
        </tr>
      </thead>
      <tbody>
        {channels.map((channel, idx) => {
          const { ch, name, value } = channel;
          const currentValue = values[ch] !== undefined ? values[ch] : value;
          const sliderRef = useRef(null);

          useEffect(() => {
            const el = sliderRef.current;
            if (!el) return;

            const handleInput = (e) => {
              const newVal = parseInt(e.target.value);
              handleValueChange(ch, newVal);
            };

            el.addEventListener("input", handleInput);
            return () => el.removeEventListener("input", handleInput);
          }, [ch]);

          return (
            <tr key={idx} className="border-t border-white/10">
              <td className="py-1">{ch}</td>
              <td className="py-1">{name}</td>
              <td className="py-1">
                <div className="flex items-center gap-2">
                  <input
                    ref={sliderRef}
                    type="range"
                    min={0}
                    max={255}
                    value={currentValue}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <span className="w-8 text-xs text-right text-gray-300">{currentValue}</span>
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
