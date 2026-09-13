import React from 'react'
import type {Auth} from './types'
import {Sidebar} from './Sidebar'
import {Topbar} from './Topbar'
export function AppShell({page,auth,onSelect,onProfile,onLogout,children}:{page:string,auth:Auth,onSelect:(page:string)=>void,onProfile:()=>void,onLogout:()=>void,children:React.ReactNode}){
 return <div className="app-layout"><Sidebar page={page} onSelect={onSelect}/><div className="workspace"><Topbar page={page} auth={auth} onProfile={onProfile} onLogout={onLogout}/>{children}</div></div>
}
