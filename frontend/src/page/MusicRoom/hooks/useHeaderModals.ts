import { useState } from 'react';

const useHeaderModals = () => {
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showExitRoomModal, setShowExitRoomModal] = useState(false);
  const [showDeleteRoomModal, setShowDeleteRoomModal] = useState(false);

  return {
    showInviteModal,
    showExitRoomModal,
    showDeleteRoomModal,
    setShowInviteModal,
    setShowExitRoomModal,
    setShowDeleteRoomModal,
    openInviteModal: () => setShowInviteModal(true),
    openDeleteModal: () => setShowDeleteRoomModal(true),
    openExitModal: () => setShowExitRoomModal(true),
  };
};

export default useHeaderModals;
