import { useEffect, useState } from 'preact/hooks';

export default function Chasers({ currentTime, insertChaser, chasers }) {
  const [templates, setTemplates] = useState([]);
  const [selected, setSelected] = useState(null);
  const [parameters, setParameters] = useState({});

  useEffect(() => {
    setTemplates(chasers);
  }, [chasers]);

  const selectedTemplate = templates.find(t => t.name === selected);

  useEffect(() => {
    if (selectedTemplate) {
      const initial = {};
      for (const [key, val] of Object.entries(selectedTemplate.parameters || {})) {
        initial[key] = val;
      }
      setParameters(initial);
    }
  }, [selected]);

  const handleParamChange = (key, value) => {
    setParameters(prev => ({
      ...prev,
      [key]: isNaN(value) ? value : parseFloat(value)
    }));
  };

  const handleInsert = () => {
    if (!selectedTemplate) return;

    const chaser_id = `chaser_${selectedTemplate.name.replace(/\s+/g, "_").toLowerCase()}_${Date.now()}`;
    insertChaser({
      chaser: selectedTemplate.name,
      time: currentTime,
      parameters,
      chaser_id
    });
  };

  return (
    <div className="bg-white/10 p-2 mb-6">
      <h2 className="text-xl font-semibold mb-4">✨ Chaser</h2>

      {templates.length === 0 ? (
        <div className="text-sm text-gray-400">No chasers defined</div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {templates.map(c => (
              <button
                key={c.name}
                className={`px-2 py-1 rounded ${selected === c.name ? 'bg-blue-600 text-white' : 'bg-gray-300 text-black'}`}
                onClick={() => setSelected(c.name)}
              >
                {c.name}
              </button>
            ))}
          </div>

          {selectedTemplate && Object.keys(parameters).length > 0 && (
            <div className="bg-black/10 p-1 rounded text-sm">
              <h3 className="font-semibold mb-2 text-white/90">Parameters</h3>
              {Object.entries(parameters).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2 mb-1">
                  <label className="w-32 text-white">{key}</label>
                  <input
                    type="number"
                    value={val}
                    onChange={(e) => handleParamChange(key, e.target.value)}
                    className="bg-gray-800 p-1 rounded text-white"
                  />
                </div>
              ))}
              <button
                className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-white"
                onClick={handleInsert}
                disabled={!selected}
              >
                ➕ Insert at {currentTime.toFixed(2)}s
              </button>

            </div>
          )}
        </div>
      )}
    </div>
  );
}
