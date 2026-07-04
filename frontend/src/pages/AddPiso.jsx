import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPiso } from '../api/client'

export default function AddPiso() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showOptional, setShowOptional] = useState(false)
  const [form, setForm] = useState({
    precio: '', metros: '', habitaciones: '', direccion: '',
    link: '', notas: '', planta: '', ascensor: '', terraza: '', parking: '', anyo_construccion: ''
  })

  function handleChange(e) {
    const { name, value, type, checked } = e.target
    setForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }))
  }

  async function handleSubmit() {
    if (!form.precio || !form.metros || !form.habitaciones || !form.direccion) {
      alert('Please fill in all required fields')
      return
    }
    setLoading(true)
    try {
      const payload = {
        precio: Number(form.precio),
        metros: Number(form.metros),
        habitaciones: Number(form.habitaciones),
        direccion: form.direccion,
        link: form.link || null,
        notas: form.notas || null,
        planta: form.planta ? Number(form.planta) : null,
        ascensor: form.ascensor === '' ? null : Boolean(form.ascensor),
        terraza: form.terraza === '' ? null : Boolean(form.terraza),
        parking: form.parking === '' ? null : Boolean(form.parking),
        anyo_construccion: form.anyo_construccion ? Number(form.anyo_construccion) : null,
      }
      const res = await createPiso(payload)
      navigate(`/piso/${res.data.id}`)
    } catch (e) {
      alert('Error creating flat')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>Add flat</h1>

      <div className="card">
        <p style={{ fontWeight: 700, marginBottom: '1rem' }}>Required info</p>

        <div className="form-group">
          <label>Price (€)</label>
          <input name="precio" type="number" value={form.precio} onChange={handleChange} placeholder="300000" />
        </div>
        <div className="form-group">
          <label>Size (m²)</label>
          <input name="metros" type="number" value={form.metros} onChange={handleChange} placeholder="75" />
        </div>
        <div className="form-group">
          <label>Bedrooms</label>
          <input name="habitaciones" type="number" value={form.habitaciones} onChange={handleChange} placeholder="3" />
        </div>
        <div className="form-group">
          <label>Address</label>
          <input name="direccion" value={form.direccion} onChange={handleChange} placeholder="Street 365, City" />
        </div>
        <div className="form-group">
          <label>Listing URL (optional)</label>
          <input name="link" value={form.link} onChange={handleChange} placeholder="https://idealista.com/..." />
        </div>
        <div className="form-group">
          <label>Notes (optional)</label>
          <textarea name="notas" value={form.notas} onChange={handleChange} rows={3} placeholder="Anything worth remembering..." />
        </div>
      </div>

      <div className="card">
        <button
          className="btn btn-secondary"
          onClick={() => setShowOptional(!showOptional)}
          style={{ width: '100%' }}
        >
          {showOptional ? '▲ Hide' : '▼ Add comfort details (optional)'}
        </button>

        {showOptional && (
          <div style={{ marginTop: '1rem' }}>
            <div className="form-group">
              <label>Floor</label>
              <input name="planta" type="number" value={form.planta} onChange={handleChange} placeholder="3" />
            </div>
            <div className="form-group">
              <label>Year built</label>
              <input name="anyo_construccion" type="number" value={form.anyo_construccion} onChange={handleChange} placeholder="2005" />
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem' }}>
              {[
                { name: 'ascensor', label: 'Elevator' },
                { name: 'terraza', label: 'Terrace' },
                { name: 'parking', label: 'Parking' },
              ].map(({ name, label }) => (
                <label key={name} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                  <input type="checkbox" name={name} checked={!!form[name]} onChange={handleChange} style={{ width: 'auto' }} />
                  {label}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button onClick={handleSubmit} className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save flat'}
        </button>
        <button onClick={() => navigate('/')} className="btn btn-secondary">Cancel</button>
      </div>
    </div>
  )
}
