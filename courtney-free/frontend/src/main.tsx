import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
function App(){
  const [token,setToken] = React.useState('')
  const [email,setEmail] = React.useState('')
  const [password,setPassword] = React.useState('')
  const [symbols,setSymbols] = React.useState('')
  const [emails,setEmails] = React.useState('')
  const headers = token ? { 'Authorization': 'Bearer ' + token } : {}
  const doLogin = async () => {
    const r = await fetch(API + '/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password})})
    const j = await r.json(); if(j.access_token){ setToken(j.access_token) } else { alert('Login failed') }
  }
  const saveWatch = async () => {
    await fetch(API + '/api/watchlist', {method:'POST', headers:{'Content-Type':'application/json', ...headers}, body: JSON.stringify({symbols: symbols.split(/\s*,\s*/).filter(Boolean)})})
    alert('Saved watchlist')
  }
  const saveEmails = async () => {
    await fetch(API + '/api/emails', {method:'POST', headers:{'Content-Type':'application/json', ...headers}, body: JSON.stringify({emails: emails.split(/\s*,\s*/).filter(Boolean)})})
    alert('Saved emails')
  }
  return (<div className="min-h-screen bg-slate-50 text-slate-900">
    <div className="max-w-2xl mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Courtney Signals</h1>
      <div className="bg-white rounded-2xl shadow p-6 space-y-4">
        <h2 className="text-xl font-semibold">Login</h2>
        <input className="border p-2 w-full rounded" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="border p-2 w-full rounded" placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="px-4 py-2 rounded bg-black text-white" onClick={doLogin}>Login</button>
      </div>
      <div className="bg-white rounded-2xl shadow p-6 space-y-4 mt-6">
        <h2 className="text-xl font-semibold">Watchlist (max 15)</h2>
        <input className="border p-2 w-full rounded" placeholder="e.g., TCS, INFY, RELIANCE" value={symbols} onChange={e=>setSymbols(e.target.value)} />
        <button className="px-4 py-2 rounded bg-black text-white" onClick={saveWatch}>Save</button>
      </div>
      <div className="bg-white rounded-2xl shadow p-6 space-y-4 mt-6">
        <h2 className="text-xl font-semibold">Emails (comma separated)</h2>
        <input className="border p-2 w-full rounded" placeholder="a@b.com, c@d.com" value={emails} onChange={e=>setEmails(e.target.value)} />
        <button className="px-4 py-2 rounded bg-black text-white" onClick={saveEmails}>Save</button>
      </div>
      <div className="bg-white rounded-2xl shadow p-6 space-y-4 mt-6">
        <h2 className="text-xl font-semibold">Manual EOD Run</h2>
        <p>Ask admin to set GitHub Action or visit /api/run_eod?secret=... on backend.</p>
      </div>
    </div>
  </div>)
}
createRoot(document.getElementById('root')!).render(<App />)