import { useState } from 'react';

interface Song {
  id: string;
  title: string;
  artist: string;
  addedBy: string;
  url: string;
}

const QueueBoard = () => {
  const [queue] = useState<Song[]>([
    {
      id: '1',
      title: 'Song Title 1',
      artist: 'Artist Name',
      addedBy: 'User1',
      url: 'https://example.com',
    },
    {
      id: '2',
      title: 'Song Title 2',
      artist: 'Artist Name',
      addedBy: 'User2',
      url: 'https://example.com',
    },
  ]);

  return (
    <div className="flex w-80 flex-col gap-6">
      <div className="flex flex-1 flex-col rounded-3xl border border-gray-200 bg-white p-6 shadow-lg transition-shadow hover:shadow-xl">
        <div className="mb-6 flex items-center gap-3 border-b border-gray-100 pb-4">
          <h2 className="text-sm uppercase tracking-wide text-gray-900">
            Queue
          </h2>
          <span className="text-xs text-gray-400">{queue.length}</span>
        </div>
        <div className="flex-1 space-y-2 overflow-y-auto">
          {queue.map((song, index) => (
            <div
              key={song.id}
              className="group cursor-pointer rounded-2xl p-4 transition-all hover:bg-gray-50"
            >
              <div className="flex items-start gap-3">
                <span className="mt-0.5 w-6 font-mono text-xs text-gray-400">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-gray-900">{song.title}</p>
                  <p className="mt-0.5 truncate text-xs text-gray-500">
                    {song.artist}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {queue.length === 0 && (
            <div className="py-20 text-center">
              <p className="text-xs text-gray-400">Empty queue</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QueueBoard;
