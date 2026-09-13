import {useMemo,useState,type FormEvent} from 'react'
import {Modal,ModalBody,ModalFooter,ModalFormError,ModalHeader} from '../modal'
import {CARD_INSTITUTIONS,CARD_NETWORKS,cardInstitution} from '../../domain/cardInstitutions'

export type CardDraft={
 id?:string;version?:number;name:string;institution_key:string;institution:string;network:string|null;
 last_four:string|null;holder_id:string;closing_day:number;due_day:number
}
type Member={id:string;name:string}

export function CardFormModal({open,initial,members,onClose,onSubmit,busy=false,error=''}:{open:boolean;initial:CardDraft;members:Member[];onClose:()=>void;onSubmit:(card:CardDraft)=>void;busy?:boolean;error?:string}){
 const [form,setForm]=useState(initial),[query,setQuery]=useState(''),[localError,setLocalError]=useState('')
 const institution=cardInstitution(form.institution_key)
 const matches=useMemo(()=>{
  const needle=query.trim().toLocaleLowerCase('pt-BR')
  if(!needle)return CARD_INSTITUTIONS
  return CARD_INSTITUTIONS.filter(item=>[item.label,...item.aliases].some(value=>value.toLocaleLowerCase('pt-BR').includes(needle)))
 },[query])
 const update=(change:Partial<CardDraft>)=>{setForm(current=>({...current,...change}));setLocalError('')}
 const choose=(key:string)=>{
  const selected=cardInstitution(key)
  update({institution_key:key,institution:key==='other'?'':selected.label})
 }
 const submit=(event:FormEvent)=>{
  event.preventDefault()
  if(!form.name.trim()){setLocalError('Informe o nome do cartão.');return}
  if(form.institution_key==='other'&&!form.institution.trim()){setLocalError('Informe o nome da instituição.');return}
  if(form.last_four&&!/^\d{4}$/.test(form.last_four)){setLocalError('O final deve ter exatamente 4 dígitos.');return}
  onSubmit({...form,name:form.name.trim(),institution:form.institution.trim(),last_four:form.last_four||null,network:form.network||null})
 }
 return <Modal open={open} onClose={onClose} busy={busy}>
  <ModalHeader description="Guarde somente dados de identificação, nunca o número completo ou CVV.">{form.id?'Editar cartão':'Novo cartão'}</ModalHeader>
  <ModalBody><form id="card-form" onSubmit={submit}>
   <label>Nome do cartão<input required maxLength={200} value={form.name} onChange={event=>update({name:event.target.value})}/></label>
   <fieldset style={{border:0,padding:0,margin:0,display:'grid',gap:10}}><legend style={{fontWeight:600,fontSize:13,marginBottom:7}}>Instituição</legend>
    <label>Buscar instituição<input type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="Busque por nome"/></label>
    <div className="card-institution-options">{matches.map(item=><button type="button" key={item.key} aria-pressed={form.institution_key===item.key} onClick={()=>choose(item.key)}>{item.label}</button>)}</div>
   </fieldset>
   {form.institution_key==='other'&&<label>Nome da instituição<input maxLength={100} value={form.institution} onChange={event=>update({institution:event.target.value})}/></label>}
   <div aria-label="Prévia do cartão" className="card-form-preview" style={{background:institution.theme.background,color:institution.theme.text,outlineColor:institution.theme.focusRing}}>
    <span>{form.institution_key==='other'?(form.institution||institution.label):institution.label}</span><strong>{form.name||'Apelido do cartão'}</strong><small style={{color:institution.theme.mutedText}}>{form.last_four?`•••• ${form.last_four}`:'Final opcional'} · {form.network?CARD_NETWORKS.find(item=>item.key===form.network)?.label:'Bandeira opcional'}</small>
   </div>
   <div className="grid two"><label>Bandeira<select value={form.network??''} onChange={event=>update({network:event.target.value||null})}><option value="">Não informar</option>{CARD_NETWORKS.map(item=><option key={item.key} value={item.key}>{item.label}</option>)}</select></label><label>Final do cartão<input inputMode="numeric" maxLength={4} value={form.last_four??''} onChange={event=>update({last_four:event.target.value||null})} placeholder="0000"/></label></div>
   <label>Titular<select value={form.holder_id} onChange={event=>update({holder_id:event.target.value})}>{members.map(person=><option key={person.id} value={person.id}>{person.name}</option>)}</select></label>
   <div className="grid two"><label>Dia do fechamento<input required type="number" min="1" max="31" value={form.closing_day} onChange={event=>update({closing_day:Number(event.target.value)})}/></label><label>Dia do vencimento<input required type="number" min="1" max="31" value={form.due_day} onChange={event=>update({due_day:Number(event.target.value)})}/></label></div>
   <ModalFormError message={localError||error}/>
  </form></ModalBody>
  <ModalFooter><button type="button" onClick={onClose}>Cancelar</button><button className="primary" form="card-form">{busy?'Salvando…':'Salvar cartão'}</button></ModalFooter>
 </Modal>
}
