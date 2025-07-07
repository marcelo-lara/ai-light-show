import { useState } from 'preact/hooks';
import FixtureCard from './FixtureCard';

export default function Fixtures({ fixtures, currentTime, fixturesPresets, addCue, previewDmx }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-6">
      <h2 
        className="text-2xl font-bold mb-4 cursor-pointer hover:text-gray-300 flex items-center gap-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="text-sm">{isExpanded ? '⌄' : '⌃'}</span>
        Fixtures
      </h2>
      {isExpanded && (
        <>
          {fixtures.length === 0 ? (
            <div className="text-sm text-gray-500 italic">No fixtures loaded</div>
          ) : (
            fixtures.map((fixture) => (
              <FixtureCard 
                key={fixture.id} 
                fixture={fixture}
                currentTime={currentTime}
                allPresets={fixturesPresets}
                addCue={addCue}
                previewDmx={previewDmx}
              />
            ))
          )}
        </>
      )}
    </div>
  );
}
