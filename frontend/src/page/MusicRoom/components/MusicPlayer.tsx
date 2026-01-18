import type { QueueResponse } from '@/schemas/queueSchema';
import { Play, Pause, Loader2 } from 'lucide-react';

interface MusicPlayerProps {
  currentSong: QueueResponse | undefined;
  isPlaying: boolean;
  duration: number;
  played: number;
  isReady: boolean;
  isLoadingNextSong: boolean;
  hasError: boolean;
  isHost: boolean;

  onPlay: () => void;
  onPause: () => void;
  onSeek: (amount: number) => void;
}

const MusicPlayer = ({
  currentSong,
  isPlaying,
  duration,
  played,
  isReady,
  isLoadingNextSong,
  hasError,
  isHost,
  onPlay,
  onPause,
  onSeek,
}: MusicPlayerProps) => {
  const currentTitle = currentSong?.title || 'No Song Selected';
  const currentArtist = currentSong?.artist || 'No Artist';

  const handlePlayPause = () => {
    if (isPlaying) {
      onPause();
    } else {
      onPlay();
    }
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const amount = parseFloat(e.target.value);
    onSeek(amount);
  };

  const formatTime = (seconds: number) => {
    if (!seconds) return '00:00';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const currentTime = duration * played;

  return (
    <div className="border-white/200 w-full rounded-3xl border bg-white/10 p-6 shadow-lg backdrop-blur-md transition-all hover:bg-white/15 hover:shadow-xl">
      <div className="flex flex-col gap-4">
        <div className="text-center">
          <h3 className="text-zinc text-lg font-bold">{currentTitle}</h3>

          <p className="truncate px-4 text-sm text-zinc-400">{currentArtist}</p>
        </div>

        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span className="w-10 text-right">{formatTime(currentTime)}</span>
          <div className="relative flex-1">
            {/* Background track */}
            <div className="h-1.5 w-full rounded-full bg-zinc-700" />
            {/* Filled progress */}
            <div
              className="absolute left-0 top-0 h-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-100"
              style={{ width: `${played * 100}%` }}
            />
            {/* Thumb indicator */}
            <div
              className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full bg-white shadow-md transition-all duration-100"
              style={{ left: `calc(${played * 100}% - 6px)` }}
            />
            {/* Invisible range input for interaction */}
            <input
              type="range"
              min={0}
              max={1}
              step="any"
              value={played}
              onChange={handleSeekChange}
              disabled={!isReady || !isHost}
              className="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
            />
          </div>
          <span className="w-10">{formatTime(duration)}</span>
        </div>

        <div className="flex items-center justify-center gap-6">
          <button
            onClick={handlePlayPause}
            disabled={!currentSong || !isHost}
            className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white transition-all hover:scale-105 hover:bg-indigo-500 active:scale-95 disabled:bg-zinc-700 disabled:opacity-50"
          >
            {!currentSong && hasError ? (
              <Play fill="currentColor" className="ml-1" />
            ) : isLoadingNextSong && !isReady ? (
              <Loader2 className="animate-spin" />
            ) : isPlaying ? (
              <Pause fill="currentColor" />
            ) : (
              <Play fill="currentColor" className="ml-1" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MusicPlayer;
