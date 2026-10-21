import { Routes, Route } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import OverviewPage from '../pages/OverviewPage';
import FilesPage from '../pages/FilesPage';
import PeersPage from '../pages/PeersPage';
import TransfersPage from '../pages/TransfersPage';
import ActivityPage from '../pages/ActivityPage';
import SettingsPage from '../pages/SettingsPage';
import { useAppContext } from '../context/AppContext';

export default function AppRouter() {
  const { state, removeNotification } = useAppContext();

  return (
    <Routes>
      <Route path="/" element={
        <Layout
          trackerConnected={state.trackerConnected}
          peerConnected={state.peerConnected}
          peerStatus={state.peerStatus}
          notifications={state.notifications}
          onDismissNotification={removeNotification}
        />
      }>
        <Route index element={<OverviewPage />} />
        <Route path="files" element={<FilesPage />} />
        <Route path="peers" element={<PeersPage />} />
        <Route path="transfers" element={<TransfersPage />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
