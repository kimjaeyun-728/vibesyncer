import { Routes, Route } from 'react-router-dom';
import { ROUTE_PATH } from './routePath';
import MainLayout from '../layout/MainLayout';
import Landing from '@/page/Landing/Landing';
import RoomPage from '@/page/MusicRoom/MusicRoom';

const AppRouter = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path={ROUTE_PATH.LANDING} element={<Landing />} />
        <Route path="/room/:id" element={<RoomPage />} />
      </Route>
    </Routes>
  );
};

export default AppRouter;
