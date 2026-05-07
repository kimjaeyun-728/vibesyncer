import Lottie from 'lottie-react';
import LoadingAnimation from '@/assets/lottie/Loading.json';

const Loading = ({ size = 128 }: { size?: number }) => (
  <div className="flex items-center justify-center">
    <Lottie
      animationData={LoadingAnimation}
      loop
      autoplay
      style={{ width: size, height: size }}
    />
  </div>
);

export default Loading;
