import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">🏠 Rankflat</Link>
      <Link to="/add" className="navbar-add">+ Add flat</Link>
    </nav>
  )
}
