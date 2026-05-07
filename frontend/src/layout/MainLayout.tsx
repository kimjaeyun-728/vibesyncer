import { UserContextProvider } from '@/contexts/UserContext';
import { Outlet } from 'react-router-dom';

const MainLayout = () => {
  return (
    <main>
      <UserContextProvider>
        <Outlet />
      </UserContextProvider>
    </main>
  );
};

export default MainLayout;
