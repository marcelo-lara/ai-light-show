import { useEffect, useRef, useState } from 'preact/hooks';
import { formatTime, saveToServer, SongsFolder } from "./utils";
import WaveSurfer from 'wavesurfer.js';
import Spectrogram from 'wavesurfer.js/dist/plugins/spectrogram.esm.js'
import ZoomPlugin from 'wavesurfer.js/dist/plugins/zoom.esm.js'
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.esm.js'


export default function AudioPlayer({ 
  currentSongFile, onReady,
  isPlaying, setIsPlaying,
  currentTime, setCurrentTime, 
 }) {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);
  const [showSpectrogram] = useState(false);


  useEffect(() => {
    if (!currentSongFile) return;

    const setupWaveSurfer = () => {
      wavesurferRef.current = WaveSurfer.create({
        container: containerRef.current,
        waveColor: '#555',
        progressColor: '#1d4ed8',
        height: 80,
        responsive: true,
        minPxPerSec: 100,
        autoScroll: true,
        dragToSeek: true,
        scrollParent: true, // Ensure scrollbar is always visible
        plugins: [TimelinePlugin.create()]
      });
     
      // Zoom plugin
      wavesurferRef.current.registerPlugin(
        ZoomPlugin.create({
          // the amount of zoom per wheel step, e.g. 0.5 means a 50% magnification per scroll
          scale: 0.1,
          // Optionally, specify the maximum pixels-per-second factor while zooming
          maxZoom: 500,
          // Enable zooming with the mouse wheel
          wheelZoom: true,
          // Enable scrolling
          scrollParent: true,
        }),
      )

      // Spectrogram plugin
      if (showSpectrogram) {
        wavesurferRef.current.registerPlugin(
          Spectrogram.create({
            labels: true,
            height: 200,
            splitChannels: false,
            scale: 'mel', // or 'linear', 'logarithmic', 'bark', 'erb'
            frequencyMax: 10000,
            frequencyMin: 0,
            fftSamples: 1024,
            labelsBackground: 'rgba(0, 0, 0, 0.1)',
          }),
        )
      }

      wavesurferRef.current.load(SongsFolder + currentSongFile);

      const ws = wavesurferRef.current;
      ws.on('ready', () => {onReady()});
      ws.on('finish', () => {
        setIsPlaying(false);
      });
      ws.on('pause', () => {
        const time = ws.getCurrentTime();
        setIsPlaying(false);
        setCurrentTime(time);
      });

      ws.on('play', () => {
        const time = ws.getCurrentTime();
        setIsPlaying(true);
        setCurrentTime(time);
      });

      ws.on('audioprocess', () => {
        const time = ws.getCurrentTime();
        setCurrentTime(time);
      });

      ws.on('seeking', () => {
        const time = ws.getCurrentTime();
        setCurrentTime(time);
      });

    };

    if (document.readyState === 'complete') {
      setupWaveSurfer();
    } else {
      window.addEventListener('load', setupWaveSurfer);
      return () => window.removeEventListener('load', setupWaveSurfer);
    }
  }, [currentSongFile]);

  useEffect(() => {
    if (wavesurferRef.current && currentTime !== undefined && !isPlaying) {
      wavesurferRef.current.seekTo(currentTime / wavesurferRef.current.getDuration());
    }
  }, [currentTime]);

  return (
    <>
      <div ref={containerRef} className="mb-4"/>
      <div id="song-controls" class="flex flex-col items-center">
        <div className="flex items-center gap-4 mb-4">
          {isPlaying ? 
            (<button onClick={() => wavesurferRef.current?.pause()} className="bg-yellow-500 hover:bg-yellow-600 px-4 py-2 rounded">⏸️ Pause</button>) : 
            (<button onClick={() => wavesurferRef.current?.play()} className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">▶️ Start</button>)
          }
          <button onClick={() => { wavesurferRef.current?.pause(); wavesurferRef.current?.seekTo(0); }} className="bg-gray-700 hover:bg-gray-800 px-4 py-2 rounded">⏹️ Stop</button>
          <span className="ml-4 w-6 text-gray-400">{formatTime(currentTime)}</span>
        </div>
      </div>
    </>
  );
}