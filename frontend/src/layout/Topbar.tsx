import {ChevronRight,LogOut} from 'lucide-react'
import type {Auth} from './types'
export function Topbar({page,auth,onProfile,onLogout}:{page:string,auth:Auth,onProfile:()=>void,onLogout:()=>void}){
 return <header className="topbar"><span>Finanças da família <ChevronRight size={14}/> <strong>{page}</strong></span><div className="profile"><button onClick={onLogout}><LogOut size={17}/>Sair</button><button className="profile-trigger" onClick={onProfile} aria-label={`Abrir perfil de ${auth.user.name}`}><span>{auth.user.name}</span><span className="avatar" aria-hidden>{auth.user.name[0]}</span></button></div></header>
}
