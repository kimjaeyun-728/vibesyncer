import type { ChatMessageResponse } from '@/schemas/chatSchema';

export const getMessageId = (msg: ChatMessageResponse) => {
  const messageContent = msg.message || '';
  return `${msg.user_id}-${msg.created_at}-${msg.id}-${messageContent.slice(0, 20)}`;
};
