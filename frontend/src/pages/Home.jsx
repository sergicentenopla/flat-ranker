import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getPisos, getScoring, deletePiso } from '../api/client'

export default function Home() {
  const [pisos, setPisos] = useState([])
  const [ranking, setRanking] = useState([])
  const [loading, setLoading] = useState(true)
  const [pesos, setPesos] = useState({ valor: 40, conectividad: 40, habitabilidad: 20 })

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    setLoading(true)
    try {
      const [pisosRes, rankingRes] = await Promise.all([
        getPisos(),
        getScoring(pesos)
      ])
      setPisos(pisosRes.data)
      setRanking(rankingRes.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this flat?')) return
    await deletePiso(id)
    fetchData()
  }

  async function handlePesosChange(nuevoPesos) {
    setPesos(nuevoPesos)
    try {
      const res = await getScoring(nuevoPesos)
      setRanking(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  if (loading) return <p className="loading">Loading flats...</p>

  if (pisos.length === 0) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <h2>No flats yet</h2>
      <p style={{ color: '#868e96', margin: '1rem 0' }}>Add your first flat to start comparing</p>
      <Link to="/add" className="btn btn-primary">+ Add flat</Link>
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem' }}>Your ranking</h1>
        <Link to="/add" className="btn btn-primary">+ Add flat</Link>
      </div>

      {/* Sliders de pesos */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p style={{ fontWeight: 700, marginBottom: '1rem' }}>Adjust priorities</p>
        {[
          { key: 'valor', label: 'Value (price/m²)' },
          { key: 'conectividad', label: 'Connectivity (travel time)' },
          { key: 'habitabilidad', label: 'Comfort (amenities)' },
        ].map(({ key, label }) => (
          <div key={key} style={{ marginBottom: '0.8rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label>{label}</label>
              <span style={{ fontWeight: 700 }}>{pesos[key]}%</span>
            </div>
            <input
              type="range" min="0" max="100" value={pesos[key]}
              onChange={e => handlePesosChange({ ...pesos, [key]: Number(e.target.value) })}
            />
          </div>
        ))}
      </div>

      {/* Ranking */}
      {ranking.error ? (
        <div className="error">{ranking.error}</div>
      ) : (
        ranking.map((item, index) => {
          const piso = pisos.find(p => p.id === item.id)
          return (
            <div key={item.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{ color: '#868e96', fontSize: '0.85rem' }}>#{index + 1}</span>
                  <h2 style={{ fontSize: '1.1rem', margin: '0.2rem 0' }}>{item.direccion}</h2>
                  <p style={{ color: '#868e96', fontSize: '0.85rem' }}>
                    {piso?.precio?.toLocaleString()}€ · {piso?.metros}m² · {item.precio_por_metro}€/m²
                    {item.tiempo_medio_transporte !== 'Not calculated' && ` · ${item.tiempo_medio_transporte} avg`}
                  </p>
                </div>
                <span className="score-badge">{item.puntuacion}</span>
              </div>

              <div style={{ marginTop: '0.8rem' }}>
                {item.positivos.map(c => <span key={c} className="tag-positive">✔ {c}</span>)}
                {item.negativos.map(c => <span key={c} className="tag-negative">✘ {c}</span>)}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <Link to={`/piso/${item.id}`} className="btn btn-secondary">View details</Link>
                <button onClick={() => handleDelete(item.id)} className="btn btn-danger">Delete</button>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
