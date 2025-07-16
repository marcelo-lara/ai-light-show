import { useState, useEffect } from 'preact/hooks';

export default function ActionsCard({ wsActions = [] }) {
  const [lastUpdated, setLastUpdated] = useState(null);
  
  useEffect(() => {
    if (wsActions.length > 0 || lastUpdated === null) {
      setLastUpdated(new Date());
    }
  }, [wsActions]);
  
  return (
    <div className="bg-white/10 rounded-2xl p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">⚡ Lighting Actions</h2>
        {lastUpdated && (
          <div className="text-xs text-gray-400">
            Updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {wsActions.length === 0 ? (
        <div className="text-gray-400 italic">No lighting actions available</div>
      ) : (
        <ul className="space-y-2 max-h-64 overflow-y-auto">
          {wsActions.map((action, index) => (
            <li key={index} className="bg-white/5 p-3 rounded-lg">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs text-gray-500">{action.fixture_id}</span>
                  <span className="font-medium">{action.action || 'Unnamed Action'}</span>
                  <p className="text-sm text-gray-400">{action.fixture_id || action.parameters || 'No description'}</p>
                  
                  {action.start_time !== undefined && (
                    <div className="text-xs text-cyan-400 mt-1">
                      {action.start_time.toFixed(2)}s
                      {action.duration && ` (${action.duration.toFixed(2)}s)`}
                    </div>
                  )}
                </div>
                
                <div className="flex-shrink-0">
                  <span className={`text-xs rounded-full px-2 py-1 ${
                    action.status === 'completed' ? 'bg-green-900/50' : 
                    action.status === 'pending' ? 'bg-yellow-900/50' : 
                    'bg-blue-900/50'
                  }`}>
                    {action.status || 'active'}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
