import Landing from '@/page/Landing/Landing';
import { Routes, Route } from 'react-router-dom';
import { ROUTE_PATH } from './routePath';
import MainLayout from '@/layout/MainLayout';

const AppRouter = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path={ROUTE_PATH.LANDING} element={<Landing />} />
      </Route>
    </Routes>
  );
};

export default AppRouter;
