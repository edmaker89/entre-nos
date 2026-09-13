import {useState} from 'react'
import {ShoppingBag,CalendarDays,Layers} from 'lucide-react'
import type {Auth} from '../App'
import {CommitmentForm} from './CommitmentForm'
import {ScheduledExpenseForm} from './ScheduledExpenseForm'
import {Modal,ModalBody,ModalFooter,ModalClose,ModalHeader} from './modal'
export function AddExpense({auth,month,onClose,onSaved}:{auth:Auth,month:string,onClose:()=>void,onSaved:()=>void}){
 const [mode,setMode]=useState<'purchase'|'rule'|'import'|null>(null)
 const [revision,setRevision]=useState(0),[feedback,setFeedback]=useState('')
 function saved(again=false){onSaved();if(again){setRevision(r=>r+1);setFeedback('Despesa salva. Você pode adicionar outra ou trocar o tipo.')}else onClose()}
 const common={auth,onClose,onBack:()=>{setMode(null);setFeedback('')},onSaved:saved,initialMonth:month,feedback}
 if(mode==='purchase')return <CommitmentForm key={revision} {...common}/>
 if(mode)return <ScheduledExpenseForm key={revision} {...common} mode={mode}/>
 return <Modal open onClose={onClose}><ModalHeader description="Escolha o tipo de lançamento.">Adicionar despesa</ModalHeader><ModalBody><p>O que você quer registrar?</p><div className="expense-types">{([
 ['purchase',ShoppingBag,'Compra ou despesa','Uma compra nova, à vista ou parcelada.'],
 ['rule',CalendarDays,'Conta recorrente','Aluguel, energia e outras contas que se repetem.'],
 ['import',Layers,'Parcelas em andamento','Uma compra ou financiamento que você já começou a pagar.'],
 ] as const).map(([value,Icon,title,help])=><button key={value} onClick={()=>setMode(value)}><Icon size={23}/><span><strong>{title}</strong><small>{help}</small></span></button>)}</div></ModalBody><ModalFooter><ModalClose>Fechar</ModalClose></ModalFooter></Modal>
}
