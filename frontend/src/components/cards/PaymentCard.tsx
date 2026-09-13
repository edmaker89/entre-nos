import {CreditCard,Pencil,ReceiptText} from 'lucide-react'
import {CARD_NETWORKS,cardInstitution} from '../../domain/cardInstitutions'
import './cards.css'

export type PaymentCardData={id:string;version?:number;name:string;institution_key?:string;institution:string;network?:string|null;last_four?:string|null;holder_id:string;closing_day:number;due_day:number}

export function PaymentCard({card,holderName,onEdit,onSelect}:{card:PaymentCardData;holderName:string;onEdit:(card:PaymentCardData)=>void;onSelect:(card:PaymentCardData)=>void}){
 const institution=cardInstitution(card.institution_key)
 const network=CARD_NETWORKS.find(item=>item.key===card.network)?.label
 return <article aria-label={`Cartão ${card.name}`} className="payment-card-v2" style={{background:institution.theme.background,color:institution.theme.text,aspectRatio:'85.6 / 53.98',inlineSize:'min(100%, 340px)',maxInlineSize:'100%'}}>
  <div className="payment-card-v2__top"><CreditCard aria-hidden="true"/><span>{card.institution||institution.label}</span><button type="button" aria-label={`Editar ${card.name}`} onClick={()=>onEdit(card)}><Pencil size={15}/></button></div>
  <div className="payment-card-v2__identity"><strong>{card.name}</strong><small style={{color:institution.theme.mutedText}}>{holderName}</small></div>
  <div className="payment-card-v2__metadata">{card.last_four&&<span>•••• {card.last_four}</span>}{network&&<span className="payment-card-v2__network" style={{background:institution.theme.surface}}>{network}</span>}</div>
  <div className="payment-card-v2__footer"><span>Fecha <strong>{card.closing_day}</strong></span><span>Vence <strong>{card.due_day}</strong></span><button type="button" aria-label={`Ver faturas de ${card.name}`} onClick={()=>onSelect(card)}><ReceiptText size={14}/>Faturas</button></div>
 </article>
}
