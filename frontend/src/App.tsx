import {useEffect,useState} from 'react'
import {Plus} from 'lucide-react'
import {RecurrenceManager} from './pages/RecurrenceManager'
import {Planning} from './pages/Planning'
import {Commitment} from './pages/Commitment'
import {Cards} from './pages/Cards'
import {Family} from './pages/Family'
import {AddExpense} from './components/AddExpense'
import {ProfileModal} from './components/ProfileModal'
import {today,api,createOperation} from './api/client'
import {Overview} from './pages/Overview'
import {Login} from './pages/Login'
import {AppShell} from './layout/AppShell'
import type {Auth} from './layout/types'
export type {Person,Auth} from './layout/types'
export function App(){
 const [selectedMonth,setSelectedMonth]=useState('default')
 const [detail,setDetail]=useState<string|null>(null)
 const [adding,setAdding]=useState(false),[revision,setRevision]=useState(0)
 const [auth,setAuth]=useState<Auth|null>(null),[loading,setLoading]=useState(true),[page,setPage]=useState('Resumo'),[profileOpen,setProfileOpen]=useState(false)
 const load=()=>api<Auth>('/auth/me').then(setAuth).catch(()=>setAuth(null)).finally(()=>setLoading(false))
 useEffect(()=>{load();const expired=()=>setAuth(null);window.addEventListener('session-expired',expired);return()=>window.removeEventListener('session-expired',expired)},[])
 if(loading)return <div className="loading">Preparando seu espaço…</div>
 if(!auth)return <Login onLogin={load}/>
 const logout=async()=>{await createOperation('/auth/logout','POST')();setAuth(null)}
 return <AppShell page={page} auth={auth} onSelect={setPage} onProfile={()=>setProfileOpen(true)} onLogout={()=>void logout()}><main className="main-content"><div className="page-heading"><div><span className="eyebrow">TUDO EM SEU LUGAR</span><h1>{page}</h1></div>{page!=='Família'&&<button className="primary" onClick={()=>setAdding(true)}><Plus size={18}/>Adicionar despesa</button>}</div>{page==='Família'?<Family/>:page==='Cartões'?<Cards auth={auth}/>:page==='Planejamento'?<Planning refresh={revision} auth={auth} onChanged={()=>setRevision(x=>x+1)}/>:<><Overview key={page} view={page==='Resumo'?'summary':'entries'} onShowEntries={()=>setPage('Lançamentos')} auth={auth} onOpen={setDetail} refresh={revision} selectedMonth={selectedMonth} onMonthChange={setSelectedMonth}/>{page==='Lançamentos'&&selectedMonth!=='default'&&<RecurrenceManager month={selectedMonth} refresh={revision} onChanged={()=>setRevision(x=>x+1)}/>}</>}</main>{detail&&<Commitment id={detail} onClose={()=>setDetail(null)} onChanged={()=>setRevision(x=>x+1)}/>} {adding&&<AddExpense auth={auth} month={selectedMonth==='default'?today().slice(0,7):selectedMonth} onClose={()=>setAdding(false)} onSaved={()=>setRevision(x=>x+1)}/>}<ProfileModal open={profileOpen} onClose={()=>setProfileOpen(false)} onUpdated={profile=>setAuth(current=>current?{...current,user:{...current.user,...profile},members:current.members.map(member=>member.id===profile.id?{...member,name:profile.name}:member)}:current)}/></AppShell>
}
