import {useState} from 'react'
import {monthLabel} from '../../api/client'
import {Modal,ModalBody,ModalFooter,ModalFormError,ModalHeader} from '../modal'

export type InvoiceCycle={id:string;version:number;month:string;closing_date:string;due_date:string;paid_at:string|null;confirmed:boolean}
export type ClosingPreview={changes:{commitment_id:string;first_month:string}[]}

export function InvoicePaymentModal({open,cycle,initialDate,error='',busy=false,onClose,onConfirm}:{open:boolean;cycle:InvoiceCycle;initialDate:string;error?:string;busy?:boolean;onClose:()=>void;onConfirm:(date:string)=>void}){
 const [date,setDate]=useState(initialDate)
 return <Modal open={open} onClose={onClose} busy={busy}><ModalHeader>Pagar fatura</ModalHeader><ModalBody><p>Esta ação abrange a fatura inteira.</p><label>Data do pagamento<input type="date" value={date} onChange={event=>setDate(event.target.value)}/></label><ModalFormError message={error}/></ModalBody><ModalFooter><button type="button" onClick={onClose}>Cancelar</button><button type="button" className="primary" onClick={()=>onConfirm(date)}>{busy?'Salvando…':'Confirmar pagamento'}</button></ModalFooter></Modal>
}

export function CycleClosingModal({open,cycle,preview,error='',busy=false,onClose,onPreview,onApply}:{open:boolean;cycle:InvoiceCycle;preview?:ClosingPreview;error?:string;busy?:boolean;onClose:()=>void;onPreview:(date:string)=>void;onApply:()=>void}){
 const [date,setDate]=useState(cycle.closing_date)
 return <Modal open={open} onClose={onClose} busy={busy}><ModalHeader>Conferir mudança de fechamento</ModalHeader><ModalBody>{!preview?<label>Fechamento efetivo<input type="date" value={date} onChange={event=>setDate(event.target.value)}/></label>:<><p>{preview.changes.length} compras terão a primeira competência alterada.</p><div className="preview-list">{preview.changes.map(change=><div key={change.commitment_id}><span>Compra vinculada</span><strong>{monthLabel(change.first_month.slice(0,7))}</strong></div>)}</div></>}<ModalFormError message={error}/></ModalBody><ModalFooter><button type="button" onClick={onClose}>Cancelar</button><button type="button" className="primary" onClick={preview?onApply:()=>onPreview(date)}>{busy?'Calculando…':preview?'Aplicar alteração':'Conferir fechamento'}</button></ModalFooter></Modal>
}
