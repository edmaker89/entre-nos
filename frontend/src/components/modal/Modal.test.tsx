import React,{createRef} from 'react'
import {cleanup,fireEvent,render,screen} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {
 ConfirmStep,Modal,ModalBody,ModalClose,ModalFooter,ModalFormError,ModalHeader,UnsavedChangesGuard
} from './index'

afterEach(()=>{cleanup();document.body.style.overflow=''})

function Example({onClose=vi.fn(),busy=false,closeOnEscape=true,initialFocusRef}:{onClose?:()=>void,busy?:boolean,closeOnEscape?:boolean,initialFocusRef?:React.RefObject<HTMLElement|null>}){
 return <Modal open onClose={onClose} busy={busy} closeOnEscape={closeOnEscape} initialFocusRef={initialFocusRef}>
  <ModalHeader description="Detalhes úteis">Título do modal</ModalHeader>
  <ModalBody><button>Primeiro</button><input aria-label="Campo"/><button>Último</button></ModalBody>
  <ModalFooter><button>Cancelar</button><button>Salvar</button></ModalFooter>
 </Modal>
}

describe('MODAL-01 primitive',()=>{
 it('connects dialog title and description accessibly',()=>{
  render(<Example/>)
  const dialog=screen.getByRole('dialog',{name:'Título do modal'})
  expect(dialog.getAttribute('aria-describedby')).toBe(screen.getByText('Detalhes úteis').id)
  expect(dialog.getAttribute('aria-modal')).toBe('true')
  expect((dialog as HTMLDialogElement).open).toBe(true)
  expect((dialog.querySelector('.modal__body') as HTMLElement).style.overflowY).toBe('auto')
 })

 it('moves initial focus to the first useful control',()=>{
  render(<Example/>)
  expect(document.activeElement).toBe(screen.getByRole('button',{name:'Primeiro'}))
 })

 it('honors an explicit initial focus ref',()=>{
  const ref=createRef<HTMLInputElement>()
  render(<Modal open onClose={()=>{}} initialFocusRef={ref}><ModalHeader>Título</ModalHeader><ModalBody><button>Antes</button><input ref={ref} aria-label="Preferido"/></ModalBody></Modal>)
  expect(document.activeElement).toBe(screen.getByLabelText('Preferido'))
 })

 it('restores focus to the opener after close',()=>{
  const opener=document.createElement('button');document.body.append(opener);opener.focus()
  const {rerender}=render(<Example/>)
  rerender(<Modal open={false} onClose={()=>{}}><ModalHeader>Título</ModalHeader></Modal>)
  expect(document.activeElement).toBe(opener)
  opener.remove()
 })

 it('requests close on Escape cancel event',()=>{
  const close=vi.fn();render(<Example onClose={close}/>)
  fireEvent(screen.getByRole('dialog'),new Event('cancel',{bubbles:true,cancelable:true}))
  expect(close).toHaveBeenCalledTimes(1)
 })

 it('does not close on Escape while busy or explicitly disabled',()=>{
  const busyClose=vi.fn();const fixedClose=vi.fn()
  const {unmount}=render(<Example onClose={busyClose} busy/>)
  fireEvent(screen.getByRole('dialog'),new Event('cancel',{cancelable:true}))
  expect(busyClose).not.toHaveBeenCalled()
  unmount();render(<Example onClose={fixedClose} closeOnEscape={false}/>)
  fireEvent(screen.getByRole('dialog'),new Event('cancel',{cancelable:true}))
  expect(fixedClose).not.toHaveBeenCalled()
 })

 it('closes only when the backdrop itself is clicked',()=>{
  const close=vi.fn();render(<Example onClose={close}/>)
  fireEvent.click(screen.getByRole('button',{name:'Primeiro'}))
  expect(close).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('dialog'))
  expect(close).toHaveBeenCalledTimes(1)
 })

 it('locks body scroll and restores its prior value',()=>{
  document.body.style.overflow='scroll'
  const {unmount}=render(<Example/>)
  expect(document.body.style.overflow).toBe('hidden')
  unmount()
  expect(document.body.style.overflow).toBe('scroll')
 })

 it('wraps Tab from the last control to the first',()=>{
  render(<Example/>)
  const controls=screen.getAllByRole('button')
  controls.at(-1)!.focus();fireEvent.keyDown(screen.getByRole('dialog'),{key:'Tab'})
  expect(document.activeElement).toBe(controls[0])
 })

 it('wraps Shift+Tab from the first control to the last',()=>{
  render(<Example/>)
  const controls=screen.getAllByRole('button')
  controls[0].focus();fireEvent.keyDown(screen.getByRole('dialog'),{key:'Tab',shiftKey:true})
  expect(document.activeElement).toBe(controls.at(-1))
 })

 it('disables footer actions and announces busy state',()=>{
  render(<Example busy/>)
  expect(screen.getByRole('dialog').getAttribute('aria-busy')).toBe('true')
  expect((screen.getByRole('button',{name:'Salvar'}) as HTMLButtonElement).disabled).toBe(true)
  expect((screen.getByRole('button',{name:'Cancelar'}) as HTMLButtonElement).disabled).toBe(true)
 })

 it('ModalClose uses the shared close request',()=>{
  const close=vi.fn()
  render(<Modal open onClose={close}><ModalHeader>Aviso</ModalHeader><ModalClose>Fechar aviso</ModalClose></Modal>)
  fireEvent.click(screen.getByRole('button',{name:'Fechar aviso'}))
  expect(close).toHaveBeenCalledTimes(1)
 })

 it('focuses a newly rendered form error',()=>{
  render(<Modal open onClose={()=>{}}><ModalHeader>Formulário</ModalHeader><ModalFormError message="Revise os campos"/></Modal>)
  expect(document.activeElement).toBe(screen.getByRole('alert'))
  expect(screen.getByRole('alert').textContent).toBe('Revise os campos')
 })

 it('ConfirmStep exposes impact and invokes the explicit confirmation',()=>{
  const confirm=vi.fn();const cancel=vi.fn()
  render(<Modal open onClose={cancel}><ConfirmStep title="Excluir?" description="Todas as parcelas serão removidas." confirmLabel="Excluir compromisso" onConfirm={confirm} onCancel={cancel}/></Modal>)
  expect(screen.getByText('Todas as parcelas serão removidas.')).toBeTruthy()
  fireEvent.click(screen.getByRole('button',{name:'Excluir compromisso'}))
  expect(confirm).toHaveBeenCalledTimes(1)
  expect(cancel).not.toHaveBeenCalled()
 })

 it('UnsavedChangesGuard replaces content until discard is confirmed',()=>{
 const discard=vi.fn()
  render(<Modal open onClose={()=>{}}><UnsavedChangesGuard dirty onDiscard={discard}>{guard=><button onClick={guard.requestClose}>Fechar formulário</button>}</UnsavedChangesGuard></Modal>)
  fireEvent.click(screen.getByRole('button',{name:'Fechar formulário'}))
  expect(screen.getByText('Descartar alterações?')).toBeTruthy()
  fireEvent.click(screen.getByRole('button',{name:'Continuar editando'}))
  expect(screen.getByRole('button',{name:'Fechar formulário'})).toBeTruthy()
  fireEvent.click(screen.getByRole('button',{name:'Fechar formulário'}))
  fireEvent.click(screen.getByRole('button',{name:'Descartar alterações'}))
  expect(discard).toHaveBeenCalledTimes(1)
 })

 it('ships explicit viewport bounds for mobile and desktop widths',()=>{
  render(<Example/>)
  const dialog=screen.getByRole('dialog') as HTMLDialogElement
  expect(dialog.style.width).toBe('calc(100% - 20px)')
  expect(dialog.style.maxWidth).toBe('640px')
  expect(dialog.style.maxHeight).toBe('calc(100dvh - 20px)')
  expect(dialog.classList.contains('modal')).toBe(true)
 })
})
