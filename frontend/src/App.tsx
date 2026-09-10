import {CommitmentForm} from './components/CommitmentForm'
import {Overview} from './pages/Overview'
import {useEffect,useState} from 'react'
import {Layers,LogOut,LayoutDashboard,CreditCard,CalendarRange,List,Plus,ChevronRight} from 'lucide-react'
import {api,createOperation} from './api/client'
import {Login} from './pages/Login'
export type Person={id:string,name:string}
export type Auth={user:Person,members:Person[],family_id:string}
export function App(){
 const [adding,setAdding]=useState(false),[revision,setRevision]=useState(0)
 const [auth,setAuth]=useState<Auth|null>(null),[loading,setLoading]=useState(true),[page,setPage]=useState('Resumo')
 const load=()=>api<Auth>('/auth/me').then(setAuth).catch(()=>setAuth(null)).finally(()=>setLoading(false))
 useEffect(()=>{load();const expired=()=>setAuth(null);window.addEventListener('session-expired',expired);return()=>window.removeEventListener('session-expired',expired)},[])
 if(loading)return <div className="loading">Preparando seu espaço…</div>
 if(!auth)return <Login onLogin={load}/>
 const navigation=[['Resumo',LayoutDashboard],['Lançamentos',List],['Cartões',CreditCard],['Planejamento',CalendarRange]] as const
 return <div className="app-layout"><aside className="sidebar"><div className="brand"><Layers/><span>entre nós<span className="brand-dot">.</span></span></div><div className="family-pill"><div className="avatar">{auth.user.name[0]}</div><div><strong>Minha família</strong><small>Um espaço de vocês</small></div><ChevronRight size={16}/></div><span className="nav-caption">SEU PLANEJAMENTO</span><nav>{navigation.map(([name,Icon])=><button key={name} className={page===name?'active':''} onClick={()=>setPage(name)}><Icon size={19}/><span>{name}</span></button>)}</nav><div className="sidebar-foot"><p>Pequenos cuidados.<br/><strong>Grandes planos.</strong></p><button onClick={async()=>{await createOperation('/auth/logout','POST')();setAuth(null)}}><LogOut size={17}/>Sair</button></div></aside><div className="workspace"><header className="topbar"><span>Finanças da família <ChevronRight size={14}/> <strong>{page}</strong></span><div className="profile"><span>{auth.user.name}</span><div className="avatar">{auth.user.name[0]}</div></div></header><main className="main-content"><div className="page-heading"><div><span className="eyebrow">TUDO EM SEU LUGAR</span><h1>{page}</h1></div><button className="primary" onClick={()=>setAdding(true)}><Plus size={18}/>Adicionar gasto</button></div><Overview auth={auth} onOpen={()=>{}} refresh={revision}/></main></div>{adding&&<CommitmentForm auth={auth} onClose={()=>setAdding(false)} onSaved={()=>{setAdding(false);setRevision(x=>x+1)}}/>}</div>
}
