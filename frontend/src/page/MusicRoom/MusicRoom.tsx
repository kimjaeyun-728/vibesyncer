import { useNavigate, useParams } from 'react-router-dom';
import { Users, UserPlus } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import InviteFriendModal from './components/InviteFriendModal';
import ChatBoard from './components/ChatBoard';
import QueueBoard from './components/QueueBoard';
import { useUser } from '@/contexts/UserContext';
import ExitRoomModal from './components/ExitRoomModal';
import DeleteRoomModal from './components/DeleteRoomModal';
import useRoomInfos from '@/hooks/queries/useRoomInfos';
import ErrorBoundary from '@/components/ErrorBoundary';
import Loading from '@/components/ui/Loading';
import Error from '@/components/ui/Error';
import ReactPlayer from 'react-player';
import type { OnProgressProps } from 'react-player/base';
import useWebSocket from '@/hooks/useWebSocket';
import useQueueList from '@/hooks/queries/useQueueList';
import MusicPlayer from './components/MusicPlayer';
import AlbumCover from './components/AlbumCover';
import usePatchQueueItem from '@/hooks/mutations/usePatchQueueItem';

const MusicRoom = () => {
  const navigate = useNavigate();
  const { id: roomCode } = useParams();
  const { user } = useUser();
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showExitRoomModal, setShowExitRoomModal] = useState(false);
  const [showDeleteRoomModal, setShowDeleteRoomModal] = useState(false);

  const { data: roomInfos, isLoading, isError } = useRoomInfos(roomCode || '');
  const {
    data: queueList,
    isLoading: isQueueLoading,
    isError: isQueueError,
  } = useQueueList(roomCode || '');

  const { sendMessage, newMessage, connectionStatus, isAiLoading } =
    useWebSocket(roomCode || '');

  // ReactPlayer state
  const [isPlaying, setIsPlaying] = useState(false);
  const [played, setPlayed] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const playerRef = useRef<ReactPlayer>(null);
  const seekTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const currentSong = queueList?.[0];
  const currentSongUrl = currentSong?.music_url;
  const currentSongId = currentSong?.id || 0;

  const isValidUrl = currentSongUrl && ReactPlayer.canPlay(currentSongUrl);

  const {
    mutate: patchQueueItem,
    isPending: isPatchPending,
    isError: isPatchError,
  } = usePatchQueueItem({ roomCode: roomCode || '', currentSongId });

  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  // WebSocket sync message handling
  useEffect(() => {
    if (newMessage?.type !== 'sync') return;

    const { action, timestamp, videoId, user_id } = newMessage as any;

    if (user?.isHost && user_id === user?.userId) return;
    if (videoId !== currentSong?.music_url) return;

    const currentPlayerTime = playerRef.current?.getCurrentTime() || 0;
    queueMicrotask(() => {
      if (action === 'play') {
        setIsPlaying(true);

        if (
          timestamp !== undefined &&
          Math.abs(currentPlayerTime - timestamp) >= 2
        ) {
          playerRef.current?.seekTo(timestamp, 'seconds');
          if (duration > 0) setPlayed(timestamp / duration);
        }
      } else if (action === 'pause') {
        setIsPlaying(false);

        if (timestamp !== undefined) {
          playerRef.current?.seekTo(timestamp, 'seconds');
          if (duration > 0) setPlayed(timestamp / duration);
        }
      } else if (action === 'seek') {
        // Debounce seek operations to prevent jitter
        if (seekTimeoutRef.current) {
          clearTimeout(seekTimeoutRef.current);
        }

        seekTimeoutRef.current = setTimeout(() => {
          if (timestamp !== undefined) {
            playerRef.current?.seekTo(timestamp, 'seconds');
            if (duration > 0) setPlayed(timestamp / duration);
          }
        }, 100);
      }
    });

    return () => {
      if (seekTimeoutRef.current) {
        clearTimeout(seekTimeoutRef.current);
      }
    };
  }, [
    newMessage,
    user?.userId,
    user?.isHost,
    currentSong?.music_url,
    duration,
  ]);

  const handlePlay = () => {
    setIsPlaying(true);
    if (user?.isHost && currentSong) {
      sendMessage({
        type: 'sync',
        action: 'play',
        timestamp: played * duration,
        videoId: currentSong.music_url,
      });
    }
  };

  const handlePause = () => {
    setIsPlaying(false);
    if (user?.isHost && currentSong) {
      sendMessage({
        type: 'sync',
        action: 'pause',
        timestamp: played * duration,
        videoId: currentSong.music_url,
      });
    }
  };

  const handleSeek = (amount: number) => {
    setPlayed(amount);
    playerRef.current?.seekTo(amount, 'fraction');
    if (user?.isHost && currentSong) {
      sendMessage({
        type: 'sync',
        action: 'seek',
        timestamp: amount * duration, // fraction to seconds
        videoId: currentSong.music_url,
      });
    }
  };

  if (isError) return <Error />;

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="border-b bg-gradient-to-br from-blue-50 to-indigo-100 px-10 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <p className="text-2xl text-gray-900">VibeSyncer</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-4 py-2">
              <Users className="h-4 w-4 text-gray-400" />
              <span className="text-xs text-gray-300">
                {isLoading ? (
                  <Loading size={20} />
                ) : (
                  roomInfos?.participants.length
                )}
              </span>
            </div>
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-2 rounded-full bg-white px-5 py-2 text-sm text-black transition-all hover:bg-gray-100"
            >
              <UserPlus className="h-4 w-4" />
            </button>
            {user?.isHost ? (
              <button
                onClick={() => setShowDeleteRoomModal(true)}
                className="rounded-full border border-gray-800 bg-gray-800 px-5 py-2 text-sm text-gray-300 transition-all hover:bg-gray-600"
              >
                Delete
              </button>
            ) : (
              <button
                onClick={() => setShowExitRoomModal(true)}
                className="rounded-full border border-gray-800 bg-gray-800 px-5 py-2 text-sm text-gray-300 transition-all hover:bg-gray-600"
              >
                Back
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="bg-white-50 mx-auto flex w-full max-w-7xl flex-1 gap-6 overflow-hidden p-10">
        <ErrorBoundary>
          <QueueBoard
            queueList={queueList}
            isLoading={isQueueLoading}
            isError={isQueueError}
          />
        </ErrorBoundary>
        <div className="align-center flex flex-1 flex-col justify-center gap-4">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900">
              {isLoading ? (
                <div className="flex h-full w-full items-center justify-center">
                  <Loading />
                </div>
              ) : (
                `${roomInfos?.host_nickname}'s ${roomInfos?.name}`
              )}
            </h1>
          </div>
          <AlbumCover isPlaying={isPlaying} currentSong={currentSong} />

          {/* Hidden ReactPlayer */}
          {isValidUrl && (
            <div
              style={{
                position: 'fixed',
                bottom: 0,
                right: 0,
                width: '1px',
                height: '1px',
                opacity: 0.001,
                pointerEvents: 'none',
                zIndex: -1,
              }}
            >
              <ReactPlayer
                key={currentSongUrl}
                ref={playerRef}
                url={currentSongUrl}
                playing={isPlaying}
                width="100%"
                height="100%"
                onReady={() => setIsReady(true)}
                onDuration={(d) => setDuration(d)}
                onProgress={(state: OnProgressProps) => setPlayed(state.played)}
                onEnded={async () => {
                  if (currentSong && roomCode) {
                    patchQueueItem();
                  } else {
                    setIsPlaying(false);
                  }
                }}
                onError={() => {
                  setIsPlaying(false);
                }}
              />
            </div>
          )}

          <MusicPlayer
            currentSong={currentSong}
            isPlaying={isPlaying}
            duration={duration}
            played={played}
            isReady={isReady}
            isLoadingNextSong={isPatchPending}
            hasError={isPatchError}
            isHost={user?.isHost ?? false}
            onPlay={handlePlay}
            onPause={handlePause}
            onSeek={(amount) => {
              handleSeek(amount);
            }}
          />
        </div>
        <ErrorBoundary>
          <ChatBoard
            currentUser={user}
            roomCode={roomCode || ''}
            sendMessage={sendMessage}
            newMessage={newMessage}
            connectionStatus={connectionStatus}
            isAiLoading={isAiLoading}
          />
        </ErrorBoundary>
      </div>

      <ErrorBoundary>
        <InviteFriendModal
          open={showInviteModal}
          onOpenChange={setShowInviteModal}
          roomCode={roomCode || ''}
        />
      </ErrorBoundary>
      <ErrorBoundary>
        <DeleteRoomModal
          open={showDeleteRoomModal}
          onOpenChange={setShowDeleteRoomModal}
        />
      </ErrorBoundary>
      <ErrorBoundary>
        <ExitRoomModal
          open={showExitRoomModal}
          onOpenChange={setShowExitRoomModal}
        />
      </ErrorBoundary>
    </div>
  );
};

export default MusicRoom;
