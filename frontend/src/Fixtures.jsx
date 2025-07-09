import { useState } from 'preact/hooks';
import FixtureCard from './FixtureCard';

export default function Fixtures({ fixtures, currentTime, fixturesPresets, addCue, previewDmx }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-6">
      <h2 
        className="text-lg mb-2 font-semibold cursor-pointer hover:text-gray-300 flex items-center gap-2"
        onClick={() => setIsExpanded(!isExpanded)}
      >
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
