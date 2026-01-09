import { Send } from 'lucide-react';
import { useState } from 'react';

interface ChatMessage {
  id: string;
  sender: string;
  message: string;
  isAI: boolean;
  timestamp: Date;
}

const ChatBoard = () => {
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'User1',
      message: 'Hello!',
      isAI: false,
      timestamp: new Date(),
    },
    {
      id: '2',
      sender: 'VibeSyncer',
      message: 'Hello, enjoy your music!',
      isAI: true,
      timestamp: new Date(),
    },
  ]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        sender: 'You',
        message: message,
        isAI: false,
        timestamp: new Date(),
      };
      setChatMessages([...chatMessages, newMessage]);
      setMessage('');
    }
  };

  return (
    <div className="flex w-80 flex-col rounded-3xl border border-gray-200 bg-white shadow-lg transition-shadow hover:shadow-xl">
      <div className="border-b border-gray-100 p-6">
        <h2 className="text-sm uppercase tracking-wide text-gray-900">Chat</h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.isAI ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.isAI ? 'bg-black text-white' : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="mb-1 text-xs opacity-60">{msg.sender}</p>
              <p className="text-sm">{msg.message}</p>
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={handleSendMessage}
        className="border-t border-gray-100 p-6"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Message..."
            className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-gray-300 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-full bg-black px-5 py-3 text-white transition-all hover:bg-gray-900"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatBoard;
