import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import AddPiso from './pages/AddPiso'
import PisoDetail from './pages/PisoDetail'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/add" element={<AddPiso />} />
          <Route path="/piso/:id" element={<PisoDetail />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
