import React,{createContext,useContext,useEffect,useId,useRef,useState} from 'react'
import {createPortal} from 'react-dom'
import './modal.css'

type ModalContextValue={requestClose:()=>void;busy:boolean;titleId:string;descriptionId:string}
const ModalContext=createContext<ModalContextValue|null>(null)
const useModal=()=>{
 const context=useContext(ModalContext)
 if(!context)throw new Error('Modal components must be rendered inside Modal.')
 return context
}

const focusableSelector='button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])'

export function Modal({open,onClose,children,busy=false,closeOnEscape=true,initialFocusRef}:{open:boolean;onClose:()=>void;children:React.ReactNode;busy?:boolean;closeOnEscape?:boolean;initialFocusRef?:React.RefObject<HTMLElement|null>}){
 const dialogRef=useRef<HTMLDialogElement>(null)
 const previousFocus=useRef<HTMLElement|null>(null)
 const titleId=useId()
 const descriptionId=useId()

 useEffect(()=>{
  if(!open)return
  const dialog=dialogRef.current!
  previousFocus.current=document.activeElement as HTMLElement|null
  const previousOverflow=document.body.style.overflow
  document.body.style.overflow='hidden'
  if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','')
  const first=initialFocusRef?.current??dialog.querySelector<HTMLElement>('[data-modal-error],'+focusableSelector)
  first?.focus()
  return()=>{
   document.body.style.overflow=previousOverflow
   if(typeof dialog.close==='function'&&dialog.open)dialog.close();else dialog.removeAttribute('open')
   previousFocus.current?.focus()
  }
 },[open,initialFocusRef])

 if(!open)return null
 const requestClose=()=>{if(!busy)onClose()}
 const onKeyDown=(event:React.KeyboardEvent<HTMLDialogElement>)=>{
  if(event.key!=='Tab')return
  const controls=Array.from(event.currentTarget.querySelectorAll<HTMLElement>(focusableSelector))
  if(!controls.length)return
  const first=controls[0],last=controls.at(-1)!
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
 }
 return createPortal(
  <dialog ref={dialogRef} className="modal" style={{width:'calc(100% - 20px)',maxWidth:'640px',maxHeight:'calc(100dvh - 20px)'}} aria-modal="true" aria-labelledby={titleId} aria-describedby={descriptionId} aria-busy={busy||undefined}
   onCancel={event=>{event.preventDefault();if(closeOnEscape)requestClose()}}
   onClick={event=>{if(event.target===event.currentTarget)requestClose()}} onKeyDown={onKeyDown}>
   <div className="modal__surface">
    <ModalContext.Provider value={{requestClose,busy,titleId,descriptionId}}>{children}</ModalContext.Provider>
   </div>
  </dialog>,document.body
 )
}

export function ModalHeader({children,description}:{children:React.ReactNode;description?:React.ReactNode}){
 const {titleId,descriptionId}=useModal()
 return <header className="modal__header"><div><h2 id={titleId}>{children}</h2><p id={descriptionId} hidden={!description}>{description}</p></div></header>
}

export function ModalBody({children}:{children:React.ReactNode}){
 return <div className="modal__body" style={{overflowY:'auto'}}>{children}</div>
}

export function ModalFooter({children}:{children:React.ReactNode}){
 const {busy}=useModal()
 return <footer className="modal__footer">{React.Children.map(children,child=>React.isValidElement<{disabled?:boolean}>(child)?React.cloneElement(child,{disabled:busy||child.props.disabled}):child)}</footer>
}

export function ModalClose({children='Fechar'}:{children?:React.ReactNode}){
 const {requestClose,busy}=useModal()
 return <button type="button" disabled={busy} onClick={requestClose}>{children}</button>
}

export function ModalFormError({message}:{message?:string|null}){
 const errorRef=useRef<HTMLDivElement>(null)
 useEffect(()=>{if(message)errorRef.current?.focus()},[message])
 if(!message)return null
 return <div ref={errorRef} className="modal__error error" role="alert" tabIndex={-1} data-modal-error>{message}</div>
}

export function ConfirmStep({title,description,confirmLabel,onConfirm,onCancel,busy=false,cancelLabel='Cancelar'}:{title:string;description:string;confirmLabel:string;onConfirm:()=>void;onCancel:()=>void;busy?:boolean;cancelLabel?:string}){
 return <><ModalHeader>{title}</ModalHeader><ModalBody><p>{description}</p></ModalBody><ModalFooter><button type="button" disabled={busy} onClick={onCancel}>{cancelLabel}</button><button type="button" className="primary" disabled={busy} onClick={onConfirm}>{confirmLabel}</button></ModalFooter></>
}

type GuardActions={requestClose:()=>void}
export function UnsavedChangesGuard({dirty,onDiscard,children}:{dirty:boolean;onDiscard:()=>void;children:(actions:GuardActions)=>React.ReactNode}){
 const [confirming,setConfirming]=useState(false)
 const requestClose=()=>{if(dirty)setConfirming(true);else onDiscard()}
 if(confirming)return <ConfirmStep title="Descartar alterações?" description="As alterações não salvas serão perdidas." confirmLabel="Descartar alterações" cancelLabel="Continuar editando" onConfirm={onDiscard} onCancel={()=>setConfirming(false)}/>
 return <>{children({requestClose})}</>
}
