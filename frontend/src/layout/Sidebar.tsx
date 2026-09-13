import {CalendarRange,CreditCard,Home,Layers,LayoutDashboard,List} from 'lucide-react'

const navigation=[['Resumo',LayoutDashboard],['Lançamentos',List],['Cartões',CreditCard],['Planejamento',CalendarRange]] as const
export function Sidebar({page,onSelect}:{page:string,onSelect:(page:string)=>void}){
 return <aside className="sidebar"><div className="brand"><Layers/><span>entre nós<span className="brand-dot">.</span></span></div><button className="family-pill" onClick={()=>onSelect('Família')} aria-label="Minha família — abrir gestão"><span className="avatar"><Home size={16}/></span><span><strong>Minha família</strong><small>Um espaço de vocês</small></span><span aria-hidden>›</span></button><span className="nav-caption">SEU PLANEJAMENTO</span><nav>{navigation.map(([name,Icon])=><button key={name} className={page===name?'active':''} onClick={()=>onSelect(name)}><Icon size={19}/><span>{name}</span></button>)}<button className={`mobile-family-link ${page==='Família'?'active':''}`} onClick={()=>onSelect('Família')}><Home size={19}/><span>Família</span></button></nav><div className="sidebar-foot"><p>Pequenos cuidados.<br/><strong>Grandes planos.</strong></p></div></aside>
}
