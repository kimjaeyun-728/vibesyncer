import ErrorBoundary from '@/components/ErrorBoundary';
import Loading from '@/components/ui/Loading';
import type { RoomInfosResponse } from '@/schemas/roomSchemas';
import type { UserData } from '@/types/user';
import { Users, UserPlus } from 'lucide-react';
import InviteFriendModal from './InviteFriendModal';
import DeleteRoomModal from './DeleteRoomModal';
import ExitRoomModal from './ExitRoomModal';
import useHeaderModals from '../hooks/useHeaderModals';

interface HeaderProps {
  roomInfos: RoomInfosResponse | undefined;
  isLoading: boolean;
  user: UserData | null;
  roomCode?: string;
}

const Header = ({ roomInfos, isLoading, user, roomCode }: HeaderProps) => {
  const {
    showInviteModal,
    showExitRoomModal,
    showDeleteRoomModal,
    setShowInviteModal,
    setShowExitRoomModal,
    setShowDeleteRoomModal,
    openInviteModal,
    openDeleteModal,
    openExitModal,
  } = useHeaderModals();

  return (
    <>
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
              onClick={openInviteModal}
              className="flex items-center gap-2 rounded-full bg-white px-5 py-2 text-sm text-black transition-all hover:bg-gray-100"
            >
              <UserPlus className="h-4 w-4" />
            </button>
            {user?.isHost ? (
              <button
                onClick={openDeleteModal}
                className="rounded-full border border-gray-800 bg-gray-800 px-5 py-2 text-sm text-gray-300 transition-all hover:bg-gray-600"
              >
                Delete
              </button>
            ) : (
              <button
                onClick={openExitModal}
                className="rounded-full border border-gray-800 bg-gray-800 px-5 py-2 text-sm text-gray-300 transition-all hover:bg-gray-600"
              >
                Back
              </button>
            )}
          </div>
        </div>
      </header>

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
    </>
  );
};

export default Header;
