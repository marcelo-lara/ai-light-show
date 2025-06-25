import { formatTime, saveToServer, SongsFolder } from "./utils";
import { useEffect, useRef, useState } from 'preact/hooks';

export default function SongCues({
    delCue,
    cues,
    currentTime,
    setCurrentTime,
    updateCues
}) {

const handleCueTimeChage = (cue) => {
  cue.time = currentTime;
  const updatedCues = cues.map((item) => (item === cue ? { ...cue } : item));
  updateCues(updatedCues);
  console.log("Updating cue time to", cue.time);
}

return (
        <>
            <h2 className="text-x2 font-semibold mb-4">🎯 Song Cue</h2>

            <table className="text-sm w-full text-white">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left">time</th>
                  <th className="text-left">Fixture</th>
                  <th className="text-left">Preset</th>
                  <th className="text-left">Parameters</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cues.sort((a, b) => a.time - b.time).map((cue, idx) => (
                  <tr key={`${cue.fixture}-${cue.time}`} className="border-b border-white/10">
                    <td onClick={() => setCurrentTime(cue.time)}>{cue.time?.toFixed(2)}</td>
                    <td>{cue.fixture}</td>
                    <td>{cue.preset}</td>
                    <td className="truncate">
                      {cue.parameters && Object.entries(cue.parameters).map(([k, v]) => (
                        <span key={k} className="inline-block mr-2">{k}: {v}</span>
                      ))}
                    </td>
                    <td className="flex gap-2">
                      <button onClick={() => handleCueTimeChage(cue)} className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded">⏱️</button>
                      <button onClick={() => delCue(cue)} className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
        </>
    );

}