import { formatTime, saveToServer, SongsFolder } from "./utils";
import { useEffect, useRef, useState } from 'preact/hooks';

export default function SongCues({
    delCue,
    cues
}) {

return (
        <>
            <h2 className="text-x2 font-semibold mb-4">🎯 Song Cue</h2>

            <table className="text-sm w-full text-white">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left">time</th>
                  <th className="text-left">Fixture</th>
                  <th className="text-left">Preset</th>
                  <th className="text-left">Duration</th>
                  <th className="text-left">Parameters</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cues.map((cue, idx) => (
                  <tr key={`${cue.fixture}-${cue.time}`} className="border-b border-white/10">
                    <td>{cue.time?.toFixed(2)}</td>
                    <td>{cue.fixture}</td>
                    <td>{cue.preset}</td>
                    <td>{cue.duration?.toFixed(2)}</td>
                    <td>
                      {cue.parameters && Object.entries(cue.parameters).map(([k, v]) => (
                        <span key={k} className="inline-block mr-2">{k}: {v}</span>
                      ))}
                    </td>
                    <td className="flex gap-2">
                      <button onClick={() => delCue(cue)} className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
        </>
    );

}