import { useState } from 'preact/hooks';

export default function SongSelector({ currentSongFile, songsList, setCurrentSongFile }) {
  const [isSongsListExpanded, setIsSongsListExpanded] = useState(false);

  const sortedSongsList = [...songsList].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));

  return (
    <div>
      {currentSongFile && (
        <div
          className="text-sm text-gray-500 mb-2 cursor-pointer"
          onClick={() => setIsSongsListExpanded(!isSongsListExpanded)}
        >
          Song: <span className="font-bold">{currentSongFile}</span>
        </div>
      )}
      {isSongsListExpanded && (
        sortedSongsList.length === 0 ? (
          <div className="text-sm text-gray-500 italic">No songs available</div>
        ) : (
          <ul>
            {sortedSongsList.map((song) => (
              <li 
                key={song} 
                className={`cursor-pointer text-sm hover:text-blue-400 ${currentSongFile === song ? 'font-bold' : ''}`}
                style={{ listStyleType: 'none' }}
                onClick={() => {
                  setCurrentSongFile(song + ".mp3");
                  setIsSongsListExpanded(false);
                }}
              >
                {song}
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}
