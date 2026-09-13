import {useMemo,useState} from 'react'
import {ApiError,api,createOperation,money,monthLabel} from '../../api/client'
import {cents} from '../CommitmentForm'
import {ConfirmStep,Modal,ModalBody,ModalFooter,ModalFormError,ModalHeader} from '../modal'

type Member={id:string;name:string}
type Card={id:string;name:string}
type Share={user_id:string;weight:number}
type Part={id?:string;number:number;month:string;amount_cents:number;paid_at?:string|null}
type Commitment={id:string;version:number;description:string;category?:string|null;buyer_id:string;card_id?:string|null;purchased_at:string;total_cents:number;original_count:number;shares:Share[];installments:Part[]}
type Preview={source_version:number;preview_hash:string;before:{installments:Part[]};after:{installments:Part[]};affected_cycles:unknown[];planned_advances:unknown[]}

const decimal=(value:number)=>(value/100).toFixed(2)

export function EditCommitmentModal({open,commitment,members,cards,onClose,onSaved}:{open:boolean;commitment:Commitment;members:Member[];cards:Card[];onClose:()=>void;onSaved:()=>void}){
 const original=useMemo(()=>({description:commitment.description,category:commitment.category??'',buyer:commitment.buyer_id,card:commitment.card_id??'',date:commitment.purchased_at,total:decimal(commitment.total_cents),count:String(commitment.original_count),firstMonth:commitment.installments[0]?.month.slice(0,7)??''}),[commitment])
 const [form,setForm]=useState(original),[preview,setPreview]=useState<Preview|null>(null),[error,setError]=useState(''),[errorFields,setErrorFields]=useState<string[]>([]),[busy,setBusy]=useState(false),[confirmDiscard,setConfirmDiscard]=useState(false),[paidLock,setPaidLock]=useState(false)
 const hasPayments=commitment.installments.some(part=>Boolean(part.paid_at))
 const dirty=JSON.stringify(form)!==JSON.stringify(original)
 const update=(field:keyof typeof form,value:string)=>{setForm(current=>({...current,[field]:value}));setPreview(null);setError('');setErrorFields([])}
 const total=cents(form.total)
 const normalizedShares=()=>{
  const sourceTotal=commitment.shares.reduce((sum,share)=>sum+share.weight,0)
  let assigned=0
  return commitment.shares.map((share,index)=>{const weight=index===commitment.shares.length-1?total-assigned:Math.floor(total*share.weight/sourceTotal);assigned+=weight;return {user_id:share.user_id,weight}})
 }
 const payload=()=>({version:commitment.version,description:form.description,category:form.category||null,buyer_id:form.buyer,card_id:form.card||null,purchased_at:form.date,total_cents:total,count:Number(form.count),first_month:form.firstMonth+'-01',shares:normalizedShares()})
 const requestClose=()=>dirty?setConfirmDiscard(true):onClose()
 async function inspect(){setBusy(true);setError('');setErrorFields([]);setPaidLock(false);try{setPreview(await api(`/commitments/${commitment.id}/edit-preview`,{method:'POST',body:JSON.stringify(payload())}))}catch(cause){const typed=cause as ApiError;setError(typed.message);setErrorFields(typed.fields??[]);setPaidLock(typed.code==='paid_fields_locked')}finally{setBusy(false)}}
 async function save(){if(!preview)return;setBusy(true);setError('');try{await createOperation(`/commitments/${commitment.id}`,'PATCH',{...payload(),version:preview.source_version,preview_hash:preview.preview_hash})();onSaved()}catch(cause){const typed=cause as ApiError;setError(typed.message);setErrorFields(typed.fields??[])}finally{setBusy(false)}}
 const invalid=(field:string)=>errorFields.includes(field)||undefined
 const lockedMessage='Há pagamentos. Descrição e categoria continuam editáveis; campos que recalculam o contrato estão bloqueados.'
 if(confirmDiscard)return <Modal open={open} onClose={()=>setConfirmDiscard(false)}><ConfirmStep title="Descartar alterações?" description="As alterações não salvas serão perdidas." confirmLabel="Descartar alterações" cancelLabel="Continuar editando" onConfirm={onClose} onCancel={()=>setConfirmDiscard(false)}/></Modal>
 return <Modal open={open} onClose={requestClose} busy={busy}>
  <ModalHeader description="Confira o cronograma antes de salvar.">Editar lançamento</ModalHeader>
  <ModalBody>
   {hasPayments&&<div className="notice">{lockedMessage}</div>}
   <form onSubmit={event=>{event.preventDefault();inspect()}}>
    <label>Descrição<input required maxLength={200} value={form.description} aria-invalid={invalid('description')} onChange={event=>update('description',event.target.value)}/></label>
    <label>Categoria<input maxLength={100} value={form.category} aria-invalid={invalid('category')} onChange={event=>update('category',event.target.value)}/></label>
    <div className="grid two">
     <label>Valor total (R$)<input required type="number" min="0.01" step="0.01" disabled={hasPayments} value={form.total} aria-invalid={invalid('total_cents')} onChange={event=>update('total',event.target.value)}/></label>
     <label>Parcelas<input required type="number" min="1" max="120" disabled={hasPayments} value={form.count} aria-invalid={invalid('count')} onChange={event=>update('count',event.target.value)}/></label>
     <label>Data da compra<input required type="date" disabled={hasPayments} value={form.date} aria-invalid={invalid('purchased_at')} onChange={event=>update('date',event.target.value)}/></label>
     <label>Forma de pagamento<select disabled={hasPayments} value={form.card} aria-invalid={invalid('card_id')} onChange={event=>update('card',event.target.value)}><option value="">Pix, boleto ou débito</option>{cards.map(card=><option key={card.id} value={card.id}>{card.name}</option>)}</select></label>
     <label>Quem comprou<select disabled={hasPayments} value={form.buyer} aria-invalid={invalid('buyer_id')} onChange={event=>update('buyer',event.target.value)}>{members.map(member=><option key={member.id} value={member.id}>{member.name}</option>)}</select></label>
     <label>Primeira competência<input required type="month" disabled={hasPayments||Boolean(form.card)} value={form.firstMonth} aria-invalid={invalid('first_month')} onChange={event=>update('firstMonth',event.target.value)}/></label>
    </div>
    <ModalFormError message={error}/>{paidLock&&<p>Reabra os pagamentos no histórico para recalcular o contrato.</p>}
   </form>
   {preview&&<section aria-label="Prévia da edição"><h3>Antes e depois</h3><div className="grid two"><Schedule title="Antes" parts={preview.before.installments}/><Schedule title="Depois" parts={preview.after.installments}/></div><p>{preview.affected_cycles.length} {preview.affected_cycles.length===1?'fatura':'faturas'} serão reabertas.</p><p>{preview.planned_advances.length} {preview.planned_advances.length===1?'antecipação planejada':'antecipações planejadas'} será cancelada antes da reconstrução.</p></section>}
  </ModalBody>
  <ModalFooter><button type="button" onClick={requestClose}>Cancelar</button>{preview&&<button type="button" onClick={()=>setPreview(null)}>Editar</button>}{preview&&<button type="button" className="primary" onClick={save}>{busy?'Salvando…':'Salvar alterações'}</button>}{!preview&&<button type="button" className="primary" onClick={inspect}>{busy?'Calculando…':'Conferir alterações'}</button>}</ModalFooter>
 </Modal>
}

function Schedule({title,parts}:{title:string;parts:Part[]}){return <div className="panel"><strong>{title}</strong>{parts.map(part=><p key={`${title}-${part.number}`}>{part.number} · {monthLabel(part.month.slice(0,7))} · {money(part.amount_cents)}</p>)}</div>}
