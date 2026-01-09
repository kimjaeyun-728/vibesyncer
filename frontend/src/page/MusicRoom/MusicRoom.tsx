import { useParams, useSearchParams } from 'react-router-dom';
import { Users, UserPlus } from 'lucide-react';
import { useState } from 'react';
import InviteFriendModal from './components/InviteFriendModal';
import GoBackModal from './components/GoBackModal';
import ChatBoard from './components/ChatBoard';
import QueueBoard from './components/QueueBoard';
import AlbumCover from './components/AlbumCover';
import MusicPlayer from './components/MusicPlayer';

const MusicRoom = () => {
  const { id: roomId } = useParams();
  const [searchParams] = useSearchParams();

  const roomName = searchParams.get('roomName') || 'Room';
  const nickName = searchParams.get('nickName') || 'Room';
  const [songUrl, setSongUrl] = useState('');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showGoBackModal, setShowGoBackModal] = useState(false);
  const [isPlaying] = useState(false);
  const [currentParticipants] = useState(0);

  const handleAddSong = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="border-b bg-gradient-to-br from-blue-50 to-indigo-100 px-10 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <p className="text-2xl text-gray-900">VibeSyncer</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-gray-800 bg-gray-900 px-4 py-2">
              <Users className="h-4 w-4 text-gray-400" />
              <span className="text-xs text-gray-300">
                {currentParticipants}
              </span>
            </div>
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-2 rounded-full bg-white px-5 py-2 text-sm text-black transition-all hover:bg-gray-100"
            >
              <UserPlus className="h-4 w-4" />
            </button>
            <button
              onClick={() => setShowGoBackModal(true)}
              className="rounded-full border border-gray-800 bg-gray-800 px-5 py-2 text-sm text-gray-300 transition-all hover:bg-gray-600"
            >
              Back
            </button>
          </div>
        </div>

        <form onSubmit={handleAddSong} className="flex gap-3">
          <input
            type="url"
            value={songUrl}
            onChange={(e) => setSongUrl(e.target.value)}
            placeholder="Add song URL..."
            className="flex-1 rounded-full border bg-gray-100 px-5 py-3 text-sm text-white placeholder-gray-500 transition-all focus:border-gray-700 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-full bg-white px-8 py-3 text-sm text-black transition-all hover:bg-gray-100"
          >
            Add
          </button>
        </form>
      </header>

      <div className="bg-white-50 mx-auto flex w-full max-w-7xl flex-1 gap-6 overflow-hidden p-10">
        <QueueBoard />

        <div className="align-center flex flex-1 flex-col justify-center gap-4">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900">
              {nickName}'s {roomName}
            </h1>
          </div>
          <AlbumCover isPlaying={isPlaying} />
          <MusicPlayer
            url={
              'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'
            }
          />
        </div>

        <ChatBoard />
      </div>

      <InviteFriendModal
        open={showInviteModal}
        onOpenChange={setShowInviteModal}
        roomId={roomId || ''}
      />
      <GoBackModal open={showGoBackModal} onOpenChange={setShowGoBackModal} />
    </div>
  );
};

export default MusicRoom;
