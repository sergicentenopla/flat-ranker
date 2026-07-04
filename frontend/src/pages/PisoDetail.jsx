import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPiso, getSitios, createSitio, deleteSitio, getDistancias, updatePiso } from '../api/client'

export default function PisoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [piso, setPiso] = useState(null)
  const [sitios, setSitios] = useState([])
  const [distancias, setDistancias] = useState(null)
  const [loading, setLoading] = useState(true)
  const [calcLoading, setCalcLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [newSitio, setNewSitio] = useState({ nombre: '', direccion: '', peso: 1 })

  useEffect(() => { fetchData() }, [id])

  async function fetchData() {
    setLoading(true)
    try {
      const [pisoRes, sitiosRes] = await Promise.all([getPiso(id), getSitios(id)])
      setPiso(pisoRes.data)
      setEditForm(pisoRes.data)
      setSitios(sitiosRes.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveEdit() {
    try {
      await updatePiso(id, {
        precio: Number(editForm.precio),
        metros: Number(editForm.metros),
        habitaciones: Number(editForm.habitaciones),
        direccion: editForm.direccion,
        link: editForm.link || null,
        notas: editForm.notas || null,
        planta: editForm.planta ? Number(editForm.planta) : null,
        ascensor: editForm.ascensor ?? null,
        terraza: editForm.terraza ?? null,
        parking: editForm.parking ?? null,
        anyo_construccion: editForm.anyo_construccion ? Number(editForm.anyo_construccion) : null,
      })
      setEditing(false)
      fetchData()
    } catch (e) {
      alert('Error saving changes')
    }
  }

  async function handleAddSitio() {
    if (!newSitio.nombre || !newSitio.direccion) {
      alert('Please fill in name and address')
      return
    }
    await createSitio(id, { ...newSitio, peso: Number(newSitio.peso) })
    setNewSitio({ nombre: '', direccion: '', peso: 1 })
    fetchData()
  }

  async function handleDeleteSitio(sitioId) {
    await deleteSitio(id, sitioId)
    fetchData()
  }

  async function handleCalculate() {
    setCalcLoading(true)
    try {
      const res = await getDistancias(id)
      setDistancias(res.data)
    } catch (e) {
      alert('Error calculating distances')
    } finally {
      setCalcLoading(false)
    }
  }

  if (loading) return <p className="loading">Loading...</p>
  if (!piso) return <p className="error">Flat not found</p>

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
      <button onClick={() => navigate('/')} className="btn btn-secondary" style={{ marginBottom: '1rem' }}>
        ← Back
      </button>

      {/* Info del piso */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 style={{ fontSize: '1.3rem' }}>{piso.direccion}</h1>
          {!editing && (
            <button onClick={() => setEditing(true)} className="btn btn-secondary">Edit</button>
          )}
        </div>

        {!editing ? (
          <>
            <div style={{ display: 'flex', gap: '1.5rem', color: '#495057', fontSize: '0.95rem' }}>
              <span>💰 {piso.precio?.toLocaleString()}€</span>
              <span>📐 {piso.metros}m²</span>
              <span>🛏 {piso.habitaciones} Rooms</span>
              {piso.planta && <span>🏢 Floor {piso.planta}</span>}
            </div>
            <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
              {piso.ascensor && <span className="tag-positive">Elevator</span>}
              {piso.terraza && <span className="tag-positive">Terrace</span>}
              {piso.parking && <span className="tag-positive">Parking</span>}
            </div>
            {piso.notas && <p style={{ marginTop: '0.8rem', color: '#868e96', fontSize: '0.9rem' }}>{piso.notas}</p>}
            {piso.link && <a href={piso.link} target="_blank" rel="noreferrer" style={{ fontSize: '0.85rem', color: '#4361ee' }}>View listing ↗</a>}
          </>
        ) : (
          <div>
            <div className="form-group">
              <label>Price (€)</label>
              <input type="number" value={editForm.precio || ''} onChange={e => setEditForm(f => ({ ...f, precio: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Size (m²)</label>
              <input type="number" value={editForm.metros || ''} onChange={e => setEditForm(f => ({ ...f, metros: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Bedrooms</label>
              <input type="number" value={editForm.habitaciones || ''} onChange={e => setEditForm(f => ({ ...f, habitaciones: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Address</label>
              <input value={editForm.direccion || ''} onChange={e => setEditForm(f => ({ ...f, direccion: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Floor</label>
              <input type="number" value={editForm.planta || ''} onChange={e => setEditForm(f => ({ ...f, planta: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Year built</label>
              <input type="number" value={editForm.anyo_construccion || ''} onChange={e => setEditForm(f => ({ ...f, anyo_construccion: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Listing URL</label>
              <input value={editForm.link || ''} onChange={e => setEditForm(f => ({ ...f, link: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea rows={3} value={editForm.notas || ''} onChange={e => setEditForm(f => ({ ...f, notas: e.target.value }))} />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              {[
                { name: 'ascensor', label: 'Elevator' },
                { name: 'terraza', label: 'Terrace' },
                { name: 'parking', label: 'Parking' },
              ].map(({ name, label }) => (
                <label key={name} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={!!editForm[name]} onChange={e => setEditForm(f => ({ ...f, [name]: e.target.checked }))} style={{ width: 'auto' }} />
                  {label}
                </label>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button onClick={handleSaveEdit} className="btn btn-primary">Save</button>
              <button onClick={() => { setEditing(false); setEditForm(piso) }} className="btn btn-secondary">Cancel</button>
            </div>
          </div>
        )}
      </div>

      {/* Sitios de interés */}
      <div className="card">
        <p style={{ fontWeight: 700, marginBottom: '1rem' }}>Points of interest</p>

        {sitios.length === 0 && <p style={{ color: '#868e96', fontSize: '0.9rem', marginBottom: '1rem' }}>No points added yet</p>}

        {sitios.map(s => (
          <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid #f1f3f5' }}>
            <div>
              <span style={{ fontWeight: 600 }}>{s.nombre}</span>
              <span style={{ color: '#868e96', fontSize: '0.85rem', marginLeft: '0.5rem' }}>{s.direccion}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: '#4361ee' }}>weight: {s.peso}</span>
              <button onClick={() => handleDeleteSitio(s.id)} className="btn btn-danger" style={{ padding: '0.2rem 0.6rem', fontSize: '0.8rem' }}>✕</button>
            </div>
          </div>
        ))}

        <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 2fr auto auto', gap: '0.5rem', alignItems: 'end' }}>
          <div>
            <label>Name</label>
            <input value={newSitio.nombre} onChange={e => setNewSitio(s => ({ ...s, nombre: e.target.value }))} placeholder="Work" />
          </div>
          <div>
            <label>Address</label>
            <input value={newSitio.direccion} onChange={e => setNewSitio(s => ({ ...s, direccion: e.target.value }))} placeholder="Main Street, City" />
          </div>
          <div>
            <label>Weight</label>
            <input type="number" min="1" max="5" value={newSitio.peso} onChange={e => setNewSitio(s => ({ ...s, peso: e.target.value }))} style={{ width: '60px' }} />
          </div>
          <button onClick={handleAddSitio} className="btn btn-primary">Add</button>
        </div>
      </div>

      {/* Distancias */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <p style={{ fontWeight: 700 }}>Travel times</p>
          <button onClick={handleCalculate} className="btn btn-primary" disabled={calcLoading || sitios.length === 0}>
            {calcLoading ? 'Calculating...' : 'Calculate distances'}
          </button>
        </div>

        {distancias && distancias.distancias?.map(d => (
          <div key={d.sitio} style={{ marginBottom: '1rem' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.4rem' }}>📍 {d.sitio}</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem' }}>
              {Object.entries(d.tiempos).map(([modo, datos]) => (
                <div key={modo} style={{ background: '#f8f9fa', borderRadius: '8px', padding: '0.5rem 0.8rem', fontSize: '0.85rem' }}>
                  <span style={{ color: '#868e96' }}>{modo}</span>
                  <span style={{ float: 'right', fontWeight: 600 }}>{datos.duracion}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
