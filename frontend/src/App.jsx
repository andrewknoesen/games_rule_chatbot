import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import GamesPage from './pages/GamesPage'
import GameDetailPage from './pages/GameDetailPage'
import UploadPage from './pages/UploadPage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<GamesPage />} />
        <Route path="/games/:id" element={<GameDetailPage />} />
        <Route path="/upload" element={<UploadPage />} />
      </Routes>
    </Layout>
  )
}
