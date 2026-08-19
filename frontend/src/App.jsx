import { useState, useEffect } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState('checking...')
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status === 'ok' ? 'Connected' : 'Error'))
      .catch(() => setApiStatus('Offline / Not Connected'))
  }, [apiUrl])

  return (
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <h1>AI Meeting Intelligence & Summarization Platform</h1>
      <p style={{ color: '#94a3b8' }}>Vite + React Frontend Scaffold</p>
      <div style={{ marginTop: '2rem', padding: '1rem', background: '#1e293b', borderRadius: '8px', display: 'inline-block' }}>
        <p><strong>Backend API Status:</strong> <span style={{ color: apiStatus === 'Connected' ? '#4ade80' : '#f87171' }}>{apiStatus}</span></p>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Endpoint: {apiUrl}/health</p>
      </div>
    </div>
  )
}

export default App
