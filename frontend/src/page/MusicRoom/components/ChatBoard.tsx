import Error from '@/components/ui/Error';
import Loading from '@/components/ui/Loading';
import useChatMessages from '@/hooks/queries/useChatMessages';
import type { ChatMessageResponse } from '@/schemas/chatSchema';
import type { UserData } from '@/types/user';
import { getMessageId } from '@/utils/getMessageId';
import { useQueryClient } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';

interface ChatBoardProps {
  currentUser: UserData | null;
  roomCode: string;
  sendMessage: (messageData: object) => void;
  newMessage: ChatMessageResponse | undefined;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  isAiLoading: boolean;
}

const MAX_MESSAGE_LENGTH = 100;

const ChatBoard = ({
  currentUser,
  roomCode,
  sendMessage,
  newMessage,
  connectionStatus,
  isAiLoading,
}: ChatBoardProps) => {
  const queryClient = useQueryClient();
  const userId = currentUser?.userId;
  const [newTextInput, setNewTextInput] = useState('');

  const { data: chatMessages, isLoading, isError } = useChatMessages(roomCode);

  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (newMessage && newMessage.type === 'chat') {
      queryClient.setQueryData(
        ['chatMessages', roomCode],
        (prevMap: Map<string, ChatMessageResponse> | undefined) => {
          const updated = new Map(prevMap || []);
          updated.set(getMessageId(newMessage), newMessage);
          return updated;
        },
      );
    }
  }, [newMessage, roomCode, queryClient]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [chatMessages, isAiLoading]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newTextInput.trim();
    if (trimmed === '') return;

    if (trimmed.length > MAX_MESSAGE_LENGTH) {
      toast.error('Message too long');
      return;
    }

    if (connectionStatus !== 'connected') {
      toast.error('Not connected. Please wait...');
      return;
    }

    const messageData = {
      type: 'chat',
      message: newTextInput,
    };

    sendMessage(messageData);
    setNewTextInput('');
  };

  if (isError) return <Error />;

  return (
    <div className="flex flex-1 flex-col rounded-3xl border border-gray-200 bg-white shadow-lg transition-shadow hover:shadow-xl">
      <div className="border-b border-gray-100 p-6">
        <h2 className="text-sm uppercase tracking-wide text-gray-900">Chat</h2>
        {connectionStatus !== 'connected' && (
          <span className="text-xs text-yellow-600">
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'disconnected' && 'Disconnected'}
            {connectionStatus === 'error' && 'Connection error'}
          </span>
        )}
      </div>

      <div
        ref={chatContainerRef}
        className="scrollbar-hide flex-1 space-y-4 overflow-y-auto p-6"
      >
        {isLoading ? (
          <div className="flex h-full w-full items-center justify-center">
            <Loading />
          </div>
        ) : (
          chatMessages &&
          Array.from(chatMessages.values()).map((msg) => {
            if (msg.type === 'system') {
              return (
                <div key={getMessageId(msg)} className="flex justify-center">
                  <div className="rounded-full bg-gray-200 px-4 py-2 text-xs text-gray-500">
                    {msg.message}
                  </div>
                </div>
              );
            }

            const isMyMessage = msg.user_id === userId;

            return (
              <div
                key={getMessageId(msg)}
                className={`flex ${isMyMessage ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.user_id === 0
                      ? 'bg-black text-white'
                      : isMyMessage
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {!isMyMessage && (
                    <p className="mb-1 text-xs opacity-60">{msg.username}</p>
                  )}
                  <p className="whitespace-normal break-words text-sm">
                    {msg.message}
                  </p>
                </div>
              </div>
            );
          })
        )}

        {isAiLoading && (
          <div className="flex flex-col items-start justify-start">
            <div className="flex items-center">
              <span className="mr-[-24px] text-xs text-gray-400">
                DJ VibeBot is thinking
              </span>
              <Loading size={80} />
            </div>
          </div>
        )}
      </div>

      <form
        onSubmit={handleSendMessage}
        className="border-t border-gray-100 p-6"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={newTextInput}
            onChange={(e) => setNewTextInput(e.target.value)}
            placeholder="Message..."
            className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-gray-300 focus:outline-none"
          />
          <button
            type="submit"
            aria-label="Send message"
            className="rounded-full bg-black px-5 py-3 text-white transition-all hover:bg-gray-200"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatBoard;
