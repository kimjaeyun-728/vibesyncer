interface AlbumCoverProps {
  isPlaying: boolean;
}

const AlbumCover = ({ isPlaying }: AlbumCoverProps) => {
  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      <div
        className={`relative h-80 w-80 transition-transform duration-500 ${isPlaying ? 'scale-105' : 'scale-100'}`}
      >
        <div
          className={`h-full w-full overflow-hidden rounded-full border-[12px] border-gray-900 shadow-2xl ${isPlaying ? 'animate-spin' : ''}`}
          style={{ animationDuration: '10s' }}
        >
          <img
            src="https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=1000&auto=format&fit=crop"
            alt="Album Art"
            className="h-full w-full object-cover"
          />
        </div>
        {/* Center Hole */}
        <div className="absolute left-1/2 top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-gray-900 bg-white shadow-inner" />
      </div>
    </div>
  );
};

export default AlbumCover;
