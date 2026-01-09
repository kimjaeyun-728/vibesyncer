import { useState, useRef } from 'react';
import ReactPlayer from 'react-player';
import { Play, Pause, Loader2 } from 'lucide-react';

interface MusicPlayerProps {
  url: string;
}

export default function MusicPlayer({ url }: MusicPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [played, setPlayed] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isReady, setIsReady] = useState(false);

  const playerRef = useRef<ReactPlayer>(null);

  const handlePlayPause = () => {
    setPlaying(!playing);
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPlayed = parseFloat(e.target.value);
    setPlayed(newPlayed);
    playerRef.current?.seekTo(newPlayed, 'fraction');
  };

  // const handleProgress = (state: { played: number; loaded: number }) => {
  //   if (!playing) return;
  //   setPlayed(state.played);
  // };

  const formatTime = (seconds: number) => {
    if (!seconds) return '00:00';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const currentTime = duration * played;

  return (
    <div className="border-white-800 bg-white-900 w-full rounded-2xl border p-6 shadow-xl">
      {/* <div className="hidden">
        <ReactPlayer
          ref={playerRef}
          url={url}
          playing={playing}
          volume={0.8}
          controls={false} 
          onReady={() => setIsReady(true)}
          onDurationChange={setDuration}
          onProgress={handleProgress} 
          onEnded={() => setPlaying(false)}
        />
      </div> */}

      <div className="flex flex-col gap-4">
        <div className="text-center">
          <h3 className="text-lg font-bold text-white">Now Playing</h3>
          <p className="text-sm text-zinc-400">Streaming from URL</p>
        </div>

        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span>{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={1}
            step="any"
            value={played}
            onChange={handleSeekChange}
            className="h-1 flex-1 cursor-pointer appearance-none rounded-full bg-zinc-700 accent-indigo-500"
          />
          <span>{formatTime(duration)}</span>
        </div>

        <div className="flex items-center justify-center gap-6">
          <button
            onClick={handlePlayPause}
            disabled={!isReady}
            className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white transition-all hover:scale-105 hover:bg-indigo-500 active:scale-95 disabled:bg-zinc-700 disabled:opacity-50"
          >
            {!isReady ? (
              <Loader2 className="animate-spin" />
            ) : playing ? (
              <Pause fill="currentColor" />
            ) : (
              <Play fill="currentColor" className="ml-1" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
