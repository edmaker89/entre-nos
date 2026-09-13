import {useEffect,useState} from 'react'
import {api,createOperation} from '../api/client'
import {Modal,ModalBody,ModalClose,ModalFooter,ModalFormError,ModalHeader} from './modal'
import type {AuthUser} from '../layout/types'

type Profile=AuthUser&{email:string,version:number,email_mutable:false}
export function ProfileModal({open,onClose,onUpdated}:{open:boolean,onClose:()=>void,onUpdated:(profile:Profile)=>void}){
 const [profile,setProfile]=useState<Profile|null>(null),[name,setName]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 useEffect(()=>{if(open)api<Profile>('/profile').then(data=>{setProfile(data);setName(data.name);setError('')}).catch(error=>setError(error.message))},[open])
 const save=async()=>{if(!profile)return;setBusy(true);setError('');try{const changed=await createOperation<Profile>('/profile','PATCH',{name,version:profile.version})();setProfile(changed);onUpdated(changed);onClose()}catch(error){setError(error instanceof Error?error.message:'Não foi possível salvar seu perfil.')}finally{setBusy(false)}}
 return <Modal open={open} onClose={onClose} busy={busy}><ModalHeader description="Seus dados pessoais">Meu perfil</ModalHeader><ModalBody>{profile?<form onSubmit={event=>{event.preventDefault();void save()}}><label>Nome<input value={name} maxLength={100} onChange={event=>setName(event.target.value)}/></label><label>Email de acesso<input value={profile.email} readOnly/></label><p className="form-help">Este é o email usado para entrar. A troca de email terá verificação em uma próxima versão.</p></form>:!error&&<p>Carregando perfil…</p>}</ModalBody><ModalFormError message={error}/><ModalFooter><ModalClose>Cancelar</ModalClose><button className="primary" type="button" disabled={!profile||busy||!name.trim()} onClick={()=>void save()}>{busy?'Salvando…':'Salvar perfil'}</button></ModalFooter></Modal>
}
