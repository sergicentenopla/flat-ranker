import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
})

// Pisos
export const getPisos = () => api.get('/pisos')
export const getPiso = (id) => api.get(`/pisos/${id}`)
export const createPiso = (data) => api.post('/pisos', data)
export const updatePiso = (id, data) => api.put(`/pisos/${id}`, data)
export const deletePiso = (id) => api.delete(`/pisos/${id}`)

// Sitios de interés
export const getSitios = (pisoId) => api.get(`/pisos/${pisoId}/sitios`)
export const createSitio = (pisoId, data) => api.post(`/pisos/${pisoId}/sitios`, data)
export const deleteSitio = (pisoId, sitioId) => api.delete(`/pisos/${pisoId}/sitios/${sitioId}`)

// Distancias
export const getDistancias = (pisoId) => api.get(`/pisos/${pisoId}/distancias`)

// Scoring
export const getScoring = (pesos) => api.post('/scoring', pesos)
