import {useEffect,useState} from 'react'
import {api,createOperation} from '../api/client'
import {Modal,ModalBody,ModalClose,ModalFooter,ModalFormError,ModalHeader} from '../components/modal'
import {FamilyInviteModal,type CreatedInvite} from '../components/family/FamilyInviteModal'

export type FamilyData={family:{id:string,name:string,code:string,version:number},members:{id:string,name:string,role:'owner'|'member'}[],invites:{id:string,created_at:string,expires_at:string,status:string}[],capabilities:{manage_family:boolean,manage_invites:boolean}}
export function Family({onInviteCreated}:{onInviteCreated?:(invite:CreatedInvite)=>void}={}){
 const [data,setData]=useState<FamilyData|null>(null),[error,setError]=useState(''),[renaming,setRenaming]=useState(false),[name,setName]=useState(''),[busy,setBusy]=useState(false)
 const [createdInvite,setCreatedInvite]=useState<CreatedInvite|null>(null)
 const load=()=>api<FamilyData>('/family').then(value=>{setData(value);setName(value.family.name);setError('')}).catch(error=>setError(error.message))
 useEffect(()=>{void load()},[])
 const rename=async()=>{if(!data)return;setBusy(true);setError('');try{await createOperation('/family','PATCH',{name,version:data.family.version})();setRenaming(false);await load()}catch(error){setError(error instanceof Error?error.message:'Não foi possível renomear.')}finally{setBusy(false)}}
 const rotate=async()=>{if(!data)return;setBusy(true);setError('');try{await createOperation('/family/code/rotate','POST',{version:data.family.version})();await load()}catch(error){setError(error instanceof Error?error.message:'Não foi possível gerar o código.')}finally{setBusy(false)}}
 const invite=async()=>{setBusy(true);setError('');try{const created=await createOperation<CreatedInvite>('/family/invites','POST',{})();setCreatedInvite(created);onInviteCreated?.(created);await load()}catch(error){setError(error instanceof Error?error.message:'Não foi possível criar o convite.')}finally{setBusy(false)}}
 if(!data)return <div className="panel">{error?<div role="alert" className="error">{error}</div>:<p>Carregando família…</p>}</div>
 return <>
  <FamilyInviteModal open={createdInvite!==null} invite={createdInvite??{id:'',link:null,expires_at:'',one_time:false}} familyName={data.family.name} onClose={()=>setCreatedInvite(null)}/>
  <Modal open={renaming} onClose={()=>setRenaming(false)} busy={busy}><ModalHeader>Renomear família</ModalHeader><ModalBody><label>Nome da família<input maxLength={100} value={name} onChange={event=>setName(event.target.value)}/></label></ModalBody><ModalFormError message={error}/><ModalFooter><ModalClose>Cancelar</ModalClose><button className="primary" onClick={()=>void rename()} disabled={!name.trim()}>{busy?'Salvando…':'Salvar nome'}</button></ModalFooter></Modal>
  {error&&<div role="alert" className="error">{error}</div>}
  <section className="panel family-summary"><div><span className="eyebrow">SUA CASA FINANCEIRA</span><h2>{data.family.name}</h2><p>Código da família</p><strong className="family-code">{data.family.code}</strong></div>{data.capabilities.manage_family&&<div className="actions"><button onClick={()=>setRenaming(true)}>Renomear família</button><button disabled={busy} onClick={()=>void rotate()}>Gerar novo código</button></div>}</section>
  {!data.capabilities.manage_family&&<div className="notice">Somente o proprietário pode renomear a família, gerar códigos e convites.</div>}
  <section className="panel"><div className="row spread section-title"><h3>Integrantes</h3>{data.capabilities.manage_invites&&<button className="primary" disabled={busy} onClick={()=>void invite()}>Gerar convite</button>}</div><div className="family-members">{data.members.map(member=><div className="family-member" key={member.id}><span className="avatar">{member.name[0]}</span><strong>{member.name}</strong><span className="badge">{member.role==='owner'?'Proprietário':'Integrante'}</span>{member.role==='owner'&&<small>O proprietário não pode ser removido nesta versão.</small>}</div>)}</div></section>
  <section className="panel"><h3 className="section-title">Convites pendentes</h3>{data.invites.length?data.invites.map(invite=><div key={invite.id} className="row spread"><span>Convite pendente</span><small>Expira em {new Date(invite.expires_at).toLocaleDateString('pt-BR')}</small></div>):<p>Nenhum convite pendente.</p>}</section>
 </>
}
