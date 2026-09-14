import {useEffect,useState} from 'react'
import {Plus} from 'lucide-react'
import type {Auth} from '../App'
import {api,createOperation,monthLabel,today} from '../api/client'
import {CardFormModal,type CardDraft} from '../components/cards/CardFormModal'
import {CardsGrid} from '../components/cards/CardsGrid'
import {PaymentCard,type PaymentCardData} from '../components/cards/PaymentCard'
import {CycleClosingModal,InvoicePaymentModal,type ClosingPreview,type InvoiceCycle} from '../components/cards/CycleModals'

type CycleDialog={kind:'pay';cycle:InvoiceCycle;error:string}|{kind:'closing';cycle:InvoiceCycle;error:string;preview?:ClosingPreview;body?:{version:number;closing_date:string}}

export function Cards({auth}:{auth:Auth}){
 const [cards,setCards]=useState<PaymentCardData[]>([]),[cycles,setCycles]=useState<InvoiceCycle[]>([]),[selected,setSelected]=useState<PaymentCardData|null>(null),[form,setForm]=useState<CardDraft|null>(null),[pageError,setPageError]=useState(''),[formError,setFormError]=useState(''),[cycleDialog,setCycleDialog]=useState<CycleDialog|null>(null),[busy,setBusy]=useState(false)
 const load=()=>api<PaymentCardData[]>('/cards').then(setCards).catch(cause=>setPageError(cause.message))
 useEffect(()=>{void load()},[])
 async function select(card:PaymentCardData){setSelected(card);try{setCycles(await api(`/cards/${card.id}/cycles`))}catch(cause){setPageError((cause as Error).message)}}
 function freshCard():CardDraft{return {name:'',institution_key:'nubank',institution:'Nubank',network:null,last_four:null,holder_id:auth.user.id,closing_day:25,due_day:5}}
 function editCard(card:PaymentCardData):CardDraft{return {...card,institution_key:card.institution_key??'other',network:card.network??null,last_four:card.last_four??null}}
 async function save(card:CardDraft){setBusy(true);setFormError('');try{await createOperation(card.id?`/cards/${card.id}`:'/cards',card.id?'PATCH':'POST',card)();setForm(null);await load()}catch(cause){setFormError((cause as Error).message)}finally{setBusy(false)}}
 async function cycleAction(cycle:InvoiceCycle,action:'confirm'|'reopen'){setBusy(true);try{await createOperation(`/${action==='confirm'?'cycles':'invoices'}/${cycle.id}/${action}`,'POST',{version:cycle.version})();await select(selected!)}catch(cause){setPageError((cause as Error).message)}finally{setBusy(false)}}
 async function payInvoice(date:string){if(cycleDialog?.kind!=='pay')return;setBusy(true);try{await createOperation(`/invoices/${cycleDialog.cycle.id}/pay`,'POST',{version:cycleDialog.cycle.version,paid_at:date})();setCycleDialog(null);await select(selected!)}catch(cause){setCycleDialog({...cycleDialog,error:(cause as Error).message})}finally{setBusy(false)}}
 async function previewClosing(date:string){if(cycleDialog?.kind!=='closing')return;setBusy(true);try{const body={version:cycleDialog.cycle.version,closing_date:date};const preview=await api<ClosingPreview>(`/cycles/${cycleDialog.cycle.id}/preview-close`,{method:'POST',body:JSON.stringify(body)});setCycleDialog({...cycleDialog,body,preview,error:''})}catch(cause){setCycleDialog({...cycleDialog,error:(cause as Error).message})}finally{setBusy(false)}}
 async function applyClosing(){if(cycleDialog?.kind!=='closing'||!cycleDialog.body)return;setBusy(true);try{await createOperation(`/cycles/${cycleDialog.cycle.id}/close`,'PATCH',cycleDialog.body)();setCycleDialog(null);await select(selected!)}catch(cause){setCycleDialog({...cycleDialog,error:(cause as Error).message})}finally{setBusy(false)}}
 return <>
  {pageError&&<div className="error" role="alert">{pageError}</div>}
  <div className="row spread section-title"><p>O cartão pode ser de um. A compra fica com quem é responsável.</p><button onClick={()=>{setPageError('');setFormError('');setForm(freshCard())}}><Plus size={17}/>Novo cartão</button></div>
  <CardsGrid>{cards.map(card=><PaymentCard key={card.id} card={card} holderName={auth.members.find(person=>person.id===card.holder_id)?.name??'Titular'} onEdit={item=>{setFormError('');setForm(editCard(item))}} onSelect={item=>void select(item)}/>)}</CardsGrid>
  {!cards.length&&<div className="panel empty">Cadastre seu primeiro cartão para calcular as faturas automaticamente.</div>}
  {selected&&<section className="panel card-cycles"><h3>Faturas · {selected.name}</h3>{!cycles.length&&<p>As faturas aparecerão quando você registrar uma compra neste cartão.</p>}{cycles.map(cycle=><div className="row spread" key={cycle.id}><div><strong>{monthLabel(cycle.month.slice(0,7))}</strong><span className="subtext">Fechamento {cycle.closing_date} · Vencimento {cycle.due_date}</span><span className={'badge '+(cycle.paid_at?'':'amber')}>{cycle.paid_at?'Paga':cycle.confirmed?'Conferida':'A conferir'}</span></div><div className="actions"><button onClick={()=>setCycleDialog({kind:'closing',cycle,error:''})}>Ajustar fechamento</button><button disabled={busy} onClick={()=>void cycleAction(cycle,'confirm')}>Conferir</button><button disabled={busy} onClick={()=>cycle.paid_at?void cycleAction(cycle,'reopen'):setCycleDialog({kind:'pay',cycle,error:''})}>{cycle.paid_at?'Reabrir':'Pagar fatura'}</button></div></div>)}</section>}
  {form&&<CardFormModal open initial={form} members={auth.members} busy={busy} error={formError} onClose={()=>setForm(null)} onSubmit={card=>void save(card)}/>}
  {cycleDialog?.kind==='pay'&&<InvoicePaymentModal open cycle={cycleDialog.cycle} initialDate={today()} busy={busy} error={cycleDialog.error} onClose={()=>setCycleDialog(null)} onConfirm={date=>void payInvoice(date)}/>}
  {cycleDialog?.kind==='closing'&&<CycleClosingModal open cycle={cycleDialog.cycle} preview={cycleDialog.preview} busy={busy} error={cycleDialog.error} onClose={()=>setCycleDialog(null)} onPreview={date=>void previewClosing(date)} onApply={()=>void applyClosing()}/>}
 </>
}
