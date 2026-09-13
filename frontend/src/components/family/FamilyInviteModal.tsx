import {useState} from 'react'
import {Modal,ModalBody,ModalClose,ModalFooter,ModalFormError,ModalHeader} from '../modal'

export type CreatedInvite={id:string,link:string|null,expires_at:string,one_time:boolean}
export function FamilyInviteModal({open,invite,familyName,onClose}:{open:boolean,invite:CreatedInvite,familyName:string,onClose:()=>void}){
 const [feedback,setFeedback]=useState(''),[error,setError]=useState('')
 const message=invite.link?`Você foi convidado para participar da família ${familyName} no Entre Nós. ${invite.link}`:''
 const copy=async()=>{if(!invite.link)return;try{await navigator.clipboard.writeText(invite.link);setFeedback('Link copiado.');setError('')}catch{setError('Não foi possível copiar. Selecione o link manualmente.')}}
 const share=async()=>{if(!invite.link)return;try{if(navigator.share)await navigator.share({title:'Convite Entre Nós',text:`Participe da família ${familyName} no Entre Nós.`,url:invite.link});else await copy()}catch(error){if((error as Error).name!=='AbortError')setError('Não foi possível abrir o compartilhamento. Use WhatsApp ou copie o link.')}}
 const whatsapp=()=>{if(invite.link)window.open(`https://wa.me/?text=${encodeURIComponent(message)}`,'_blank','noopener,noreferrer')}
 return <Modal open={open} onClose={onClose}><ModalHeader description="O link aparece apenas nesta criação">Convidar para {familyName}</ModalHeader><ModalBody>{invite.link?<><label>Link do convite<input readOnly value={invite.link}/></label>{invite.link.startsWith('http://localhost')&&<div className="notice">Este link de localhost funciona somente no mesmo dispositivo/ambiente.</div>}<p>Expira em {new Date(invite.expires_at).toLocaleDateString('pt-BR')}.</p></>:<div className="notice">Este link já foi exibido. Gere um novo convite para compartilhar.</div>}{feedback&&<div role="status">{feedback}</div>}</ModalBody><ModalFormError message={error}/><ModalFooter><ModalClose>Fechar</ModalClose>{invite.link&&<><button onClick={()=>void copy()}>Copiar link</button><button onClick={whatsapp}>Enviar pelo WhatsApp</button><button className="primary" onClick={()=>void share()}>Compartilhar</button></>}</ModalFooter></Modal>
}
