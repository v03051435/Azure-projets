import { useEffect, useState } from 'react'
import './App.css'
import { apiBaseUrl, viteEnv } from '../public/config/runtimeConfig'


type Item = {
  id: number
  name: string
  description: string
}

function App() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const API_BASE_URL = apiBaseUrl();
  const VITE_ENV = viteEnv();

  useEffect(() => {
    const controller = new AbortController()
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        console.log(`Fetching data from ${API_BASE_URL}/data`)
        const res = await fetch(`${API_BASE_URL}/data`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
        const data = await res.json()
        setItems(data ?? [])
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') setError(err.message ?? String(err))
        else if (!(err instanceof Error) || err.name !== 'AbortError') setError(String(err))
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [API_BASE_URL])

  return (
    <>
      <section>
        <section className="header">
          <h1>Azure React App : OK !!!</h1>
          <p className="muted">
            OK
          </p>
        </section>
        <h2>Data from API (environment: {VITE_ENV})</h2>

        {loading && <p>Loading data...</p>}
        {error && <p className="error">Error: {error}</p>}

        {!loading && !error && (
          <div className="data-grid">
            {items.map((item) => (
              <div key={item.id} className="data-card">
                <h3>{item.name}</h3>
                <p>{item.description}</p>
                <div className="muted">ID: {item.id}</div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && items.length === 0 && <p>No items found.</p>}
      </section>
    </>
  )
}

export default App
