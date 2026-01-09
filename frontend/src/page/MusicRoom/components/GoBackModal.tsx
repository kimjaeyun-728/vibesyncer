import { ROUTE_PATH } from '@/routes/routePath';
import * as Dialog from '@radix-ui/react-dialog';
import { AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface GoBackModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const GoBackModal = ({ open, onOpenChange }: GoBackModalProps) => {
  const navigate = useNavigate();
  const handleLeaveRoom = () => {
    navigate(ROUTE_PATH.LANDING);
  };
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/60 backdrop-blur-sm" />

        <Dialog.Content className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] rounded-2xl bg-white p-6 shadow-2xl focus:outline-none">
          <div className="flex flex-col items-center text-center">
            <div className="mb-4 rounded-full bg-red-100 p-3 text-red-600">
              <AlertTriangle size={24} />
            </div>

            <Dialog.Title className="mb-2 text-lg font-bold text-gray-900">
              Leave this room?
            </Dialog.Title>

            <Dialog.Description className="mb-6 text-sm text-gray-500">
              If you leave, the music will stop playing and your connection will
              be lost.
            </Dialog.Description>

            <div className="flex w-full gap-3">
              <Dialog.Close asChild>
                <button className="flex-1 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 active:scale-[0.98]">
                  Cancel
                </button>
              </Dialog.Close>

              <button
                onClick={handleLeaveRoom}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 active:scale-[0.98]"
              >
                Leave Room
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default GoBackModal;
