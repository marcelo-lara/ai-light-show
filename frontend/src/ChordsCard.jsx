import { useEffect, useRef, useState } from 'preact/hooks';

export default function ChordsCard({ songData, currentTime, setCurrentTime }) {
  const containerRef = useRef(null);
  const [currentChordIndex, setCurrentChordIndex] = useState(-1);

  const chords = songData?.chords || [];

  useEffect(() => {
    let index = -1;
    for (let i = 0; i < chords.length; i++) {
      if (chords[i].curr_beat_time <= currentTime) {
        index = i;
      } else {
        break;
      }
    }
    setCurrentChordIndex(index);
  }, [currentTime, chords]);

  useEffect(() => {
    if (containerRef.current && currentChordIndex !== -1) {
      const rowIndex = Math.floor(currentChordIndex / 8);
      const rowEl = containerRef.current.querySelector(`#row-${rowIndex}`);
      if (rowEl) {
        rowEl.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [currentChordIndex]);

  // Group chords into rows of 8
  const groupedChords = [];
  for (let i = 0; i < chords.length; i += 8) {
    groupedChords.push(chords.slice(i, i + 8));
  }

  return (
    <>
      <h2 className="text-lg mb-2 font-semibold">Chords</h2>
      <div
        ref={containerRef}
        className="overflow-y-auto max-h-40 px-1 space-y-2"
        style={{ scrollBehavior: 'smooth' }}
      >
        {groupedChords.map((row, rowIdx) => (
          <div
            id={`row-${rowIdx}`}
            key={rowIdx}
            className="grid grid-cols-8 gap-1"
          >
            {row.map((entry, colIdx) => {
              const chordIndex = rowIdx * 8 + colIdx;
              const isCurrent = chordIndex === currentChordIndex;

              return (
                <div
                  key={colIdx}
                  className={`aspect-square flex items-center justify-center rounded text-xs font-semibold cursor-pointer ${
                    isCurrent
                      ? 'bg-gray-200 text-black'
                      : 'bg-black/30 text-gray-300 hover:bg-black/50'
                  }`}
                  onClick={() => setCurrentTime(entry.curr_beat_time)}
                >
                  {entry.chord_simple_pop}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </>
  );
}
