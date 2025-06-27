import React, { useState } from 'react';

export default function SongSelector({ currentSongFile, songsList, setCurrentSongFile }) {
  const [isSongsListExpanded, setIsSongsListExpanded] = useState(false);

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
        songsList.length === 0 ? (
          <div className="text-sm text-gray-500 italic">No songs available</div>
        ) : (
          <ul className="pl-5">
            {songsList.map((song) => (
              <li 
                key={song} 
                className={`cursor-pointer hover:text-blue-400 ${currentSongFile === song ? 'font-bold' : ''}`}
                style={{ listStyleType: 'none' }}
                onClick={() => {
                  setCurrentSongFile(song + ".mp3");
                  setIsSongsListExpanded(false);
                }}
              >
                <span className="mr-2">·</span>{song}
              </li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}
