import {useMemo,useState} from 'react'
import {ApiError,api,createOperation,money,monthLabel} from '../../api/client'
import {Modal,ModalBody,ModalFooter,ModalFormError,ModalHeader} from '../modal'
import {cents} from '../CommitmentForm'

type Member={id:string;name:string}
type Share={user_id:string;weight:number}
type Preview={source_version:number;preview_hash:string;open_total_cents:number;open_installment_count:number;months:string[];planned_advances:Array<{id:string}>}

export function TransferResponsibilityModal({open,commitmentId,version,openTotalCents,currentShares,members,onClose,onSaved}:{open:boolean;commitmentId:string;version:number;openTotalCents:number;currentShares:Share[];members:Member[];onClose:()=>void;onSaved:()=>void}){
 const currentIds=new Set(currentShares.filter(share=>share.weight>0).map(share=>share.user_id))
 const initialDestination=members.find(member=>!currentIds.has(member.id))?.id??members[0]?.id??''
 const [mode,setMode]=useState<'transfer'|'split'>('transfer'),[destination,setDestination]=useState(initialDestination),[values,setValues]=useState<Record<string,string>>({}),[preview,setPreview]=useState<Preview|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[stale,setStale]=useState(false)
 const names=useMemo(()=>new Map(members.map(member=>[member.id,member.name])),[members])
 const shares=()=>mode==='transfer'?[{user_id:destination,weight:openTotalCents}]:members.map(member=>({user_id:member.id,weight:cents(values[member.id]??'0')})).filter(share=>share.weight>0)
 const resetPreview=()=>{setPreview(null);setStale(false);setError('')}
 async function inspect(){
  const nextShares=shares(),difference=openTotalCents-nextShares.reduce((sum,share)=>sum+share.weight,0)
  if(!nextShares.length||difference){setError(`${difference>0?'Faltam':'Sobram'} ${money(Math.abs(difference))} para fechar o total aberto.`);return}
  setBusy(true);setError('');setStale(false)
  try{setPreview(await api(`/commitments/${commitmentId}/responsibility-preview`,{method:'POST',body:JSON.stringify({version,shares:nextShares})}))}catch(cause){setError((cause as Error).message)}finally{setBusy(false)}
 }
 async function save(){
  if(!preview)return
  setBusy(true);setError('')
  try{await createOperation(`/commitments/${commitmentId}/responsibility`,'POST',{source_version:preview.source_version,preview_hash:preview.preview_hash,shares:shares()})();onSaved()}
  catch(cause){const typed=cause as ApiError;setError(typed.message);setStale(typed.code==='version_conflict'||typed.code==='preview_stale')}
  finally{setBusy(false)}
 }
 const currentLabel=currentShares.map(share=>`${names.get(share.user_id)??'Integrante'} (${money(share.weight)})`).join(', ')
 return <Modal open={open} onClose={onClose} busy={busy}>
  <ModalHeader description="Somente parcelas em aberto serão alteradas.">Transferir responsabilidade</ModalHeader>
  <ModalBody>
   <p><strong>Responsável atual</strong><br/>{currentLabel||'Sem responsável informado'}</p>
   {mode==='transfer'?<label>Transferir 100% para<select value={destination} onChange={event=>{setDestination(event.target.value);resetPreview()}}>{members.map(member=><option key={member.id} value={member.id}>{member.name}</option>)}</select></label>:<fieldset><legend>Valores por responsável</legend><div className="grid two">{members.map(member=><label key={member.id}>Valor de {member.name} (R$)<input type="number" min="0" step="0.01" value={values[member.id]??''} onChange={event=>{setValues(current=>({...current,[member.id]:event.target.value}));resetPreview()}}/></label>)}</div><p className="form-help">A divisão deve somar exatamente {money(openTotalCents)}.</p></fieldset>}
   <button type="button" className="link-button" onClick={()=>{setMode(value=>value==='transfer'?'split':'transfer');resetPreview()}}>{mode==='transfer'?'Editar divisão':'Transferir 100%'}</button>
   <ModalFormError message={error}/>
   {preview&&<section className="panel" aria-label="Prévia da transferência"><h3>{preview.open_installment_count} parcelas abertas</h3><p>Total: {money(preview.open_total_cents)}</p><p>Meses: {preview.months.map(monthLabel).join(', ')}</p><p>{preview.planned_advances.length} {preview.planned_advances.length===1?'antecipação planejada':'antecipações planejadas'} também {preview.planned_advances.length===1?'será atualizada':'serão atualizadas'}.</p></section>}
  </ModalBody>
  <ModalFooter><button type="button" onClick={onClose}>Cancelar</button>{stale?<button type="button" className="primary" onClick={inspect}>Recarregar prévia</button>:preview?<button type="button" className="primary" onClick={save}>{busy?'Transferindo…':'Confirmar transferência'}</button>:<button type="button" className="primary" onClick={inspect}>{busy?'Calculando…':'Conferir transferência'}</button>}</ModalFooter>
 </Modal>
}
