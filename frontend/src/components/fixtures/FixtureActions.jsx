import { useState, useEffect } from "preact/hooks";

export default function FixtureActions({ fixture, currentTime, wsSend }) {
  const [actionParams, setActionParams] = useState({});
  const { actions = [] } = fixture;
  
  // Initialize default params for each action
  useEffect(() => {
    const initialParams = {};
    actions.forEach(action => {
      const params = {};
      // Set start_time to current time by default
      params.start_time = currentTime;
      
      // Add default values for all other parameters
      action.params.forEach(param => {
        if (param.name === 'start_time') {
          params[param.name] = currentTime;
        } else if (param.name === 'duration') {
          params[param.name] = 1.0;
        } else if (param.name === 'intensity') {
          params[param.name] = 1.0;
        } else if (param.name === 'pos_x' || param.name === 'pos_y') {
          params[param.name] = 32767; // Middle position (half of 65535)
        } else {
          params[param.name] = param.default || '';
        }
      });
      initialParams[action.name] = params;
    });
    setActionParams(initialParams);
  }, [actions, currentTime]);

  // Update start_time when currentTime changes
  useEffect(() => {
    setActionParams(prevParams => {
      const updatedParams = { ...prevParams };
      Object.keys(updatedParams).forEach(actionName => {
        if (updatedParams[actionName].start_time !== undefined) {
          updatedParams[actionName] = {
            ...updatedParams[actionName],
            start_time: currentTime
          };
        }
      });
      return updatedParams;
    });
  }, [currentTime]);

  const handleParamChange = (actionName, paramName, value) => {
    // Parse number values
    let parsedValue = value;
    if (!isNaN(parseFloat(value)) && isFinite(value)) {
      parsedValue = parseFloat(value);
    }
    
    setActionParams(prev => ({
      ...prev,
      [actionName]: {
        ...prev[actionName],
        [paramName]: parsedValue
      }
    }));
  };

  const addAction = (actionName) => {
    if (wsSend) {
      wsSend("addAction", {
        fixture_id: fixture.id,
        action: actionName,
        parameters: actionParams[actionName]
      });
    }
  };

  if (!actions || actions.length === 0) {
    return <div className="text-sm text-gray-500 italic mt-2 mb-4">No actions available</div>;
  }

  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium mb-2 text-purple-300">Actions</h4>
      <div className="space-y-4">
        {actions.map((action, idx) => (
          <div key={idx} className="bg-white/5 p-3 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium text-sm">{action.name}</span>
              <button 
                onClick={() => addAction(action.name)}
                className="bg-purple-700 hover:bg-purple-600 text-white text-xs px-2 py-1 rounded"
              >
                Add Action
              </button>
            </div>
            
            {action.params && action.params.length > 0 && (
              <div className="space-y-2">
                {action.params.map((param, pidx) => (
                  <div key={pidx} className="grid grid-cols-3 gap-2 items-center">
                    <label className="text-xs text-gray-400">{param.name}</label>
                    {param.name === 'pos_x' || param.name === 'pos_y' ? (
                      <div className="col-span-2">
                        <input 
                          type="range"
                          min="0"
                          max="65535"
                          value={actionParams[action.name]?.[param.name] || 0}
                          onChange={(e) => handleParamChange(action.name, param.name, e.target.value)}
                          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">0</span>
                          <span className="text-xs text-gray-500">{actionParams[action.name]?.[param.name] || 0}</span>
                          <span className="text-xs text-gray-500">65535</span>
                        </div>
                      </div>
                    ) : (
                      <input 
                        type="text"
                        className="col-span-2 bg-gray-800 text-white text-xs p-1 rounded"
                        value={actionParams[action.name]?.[param.name] || ''}
                        onChange={(e) => handleParamChange(action.name, param.name, e.target.value)}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
