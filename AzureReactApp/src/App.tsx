import { useEffect, useState } from 'react'
import './App.css'
import { api2BaseUrl, apiBaseUrl, viteEnv } from '../public/config/runtimeConfig'


type Item = {
  id: number
  name: string
  description: string
}

function App() {
  const [items, setItems] = useState<Item[]>([])
  const [items2, setItems2] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [loading2, setLoading2] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [error2, setError2] = useState<string | null>(null)
  const API_BASE_URL = apiBaseUrl();
  const API2_BASE_URL = api2BaseUrl();
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

  useEffect(() => {
    const controller = new AbortController()
    const load = async () => {
      try {
        setLoading2(true)
        setError2(null)
        console.log(`Fetching data from ${API2_BASE_URL}/data2`)
        const res = await fetch(`${API2_BASE_URL}/data2`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`)
        const data = await res.json()
        setItems2(data ?? [])
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') setError2(err.message ?? String(err))
        else if (!(err instanceof Error) || err.name !== 'AbortError') setError2(String(err))
      } finally {
        setLoading2(false)
      }
    }
    load()
    return () => controller.abort()
  }, [API2_BASE_URL])

  return (
    <>
      <section>
        <section className="header">
          <h1>Azure React App : Devops 第一终极版!!!</h1>
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

        <h2>Data from API2 (environment: {VITE_ENV})</h2>

        {loading2 && <p>Loading data...</p>}
        {error2 && <p className="error">Error: {error2}</p>}

        {!loading2 && !error2 && (
          <div className="data-grid">
            {items2.map((item) => (
              <div key={item.id} className="data-card">
                <h3>{item.name}</h3>
                <p>{item.description}</p>
                <div className="muted">ID: {item.id}</div>
              </div>
            ))}
          </div>
        )}

        {!loading2 && !error2 && items2.length === 0 && <p>No items found.</p>}
      </section>
    </>
  )
}

export default App
