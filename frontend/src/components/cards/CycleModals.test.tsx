import React from 'react'
import {cleanup,fireEvent,render,screen} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {CycleClosingModal,InvoicePaymentModal,type InvoiceCycle} from './CycleModals'

const cycle:InvoiceCycle={id:'cycle',version:2,month:'2026-10-01',closing_date:'2026-09-25',due_date:'2026-10-05',paid_at:null,confirmed:false}
afterEach(cleanup)

describe('CARD-UX-01 invoice modals',()=>{
 it('submits the selected invoice payment date and explains its scope',()=>{const confirm=vi.fn();render(<InvoicePaymentModal open cycle={cycle} initialDate="2026-10-06" onClose={()=>{}} onConfirm={confirm}/>);expect(screen.getByText('Esta ação abrange a fatura inteira.')).toBeTruthy();fireEvent.change(screen.getByLabelText('Data do pagamento'),{target:{value:'2026-10-07'}});fireEvent.click(screen.getByRole('button',{name:'Confirmar pagamento'}));expect(confirm).toHaveBeenCalledWith('2026-10-07')})
 it('keeps payment data and announces an API error',()=>{render(<InvoicePaymentModal open cycle={cycle} initialDate="2026-10-06" error="Falha ao pagar." onClose={()=>{}} onConfirm={()=>{}}/>);expect(screen.getByRole('alert').textContent).toBe('Falha ao pagar.');expect((screen.getByLabelText('Data do pagamento') as HTMLInputElement).value).toBe('2026-10-06')})
 it('disables payment actions while busy',()=>{render(<InvoicePaymentModal open cycle={cycle} initialDate="2026-10-06" busy onClose={()=>{}} onConfirm={()=>{}}/>);expect((screen.getByRole('button',{name:'Salvando…'}) as HTMLButtonElement).disabled).toBe(true);expect((screen.getByRole('button',{name:'Cancelar'}) as HTMLButtonElement).disabled).toBe(true)})
 it('previews a chosen closing date before allowing apply',()=>{const preview=vi.fn();render(<CycleClosingModal open cycle={cycle} onClose={()=>{}} onPreview={preview} onApply={()=>{}}/>);fireEvent.change(screen.getByLabelText('Fechamento efetivo'),{target:{value:'2026-09-20'}});fireEvent.click(screen.getByRole('button',{name:'Conferir fechamento'}));expect(preview).toHaveBeenCalledWith('2026-09-20');expect(screen.queryByRole('button',{name:'Aplicar alteração'})).toBeNull()})
 it('shows preview changes and applies only after confirmation',()=>{const apply=vi.fn();render(<CycleClosingModal open cycle={cycle} preview={{changes:[{commitment_id:'purchase',first_month:'2026-11-01'}]}} onClose={()=>{}} onPreview={()=>{}} onApply={apply}/>);expect(screen.getByText('1 compras terão a primeira competência alterada.')).toBeTruthy();expect(screen.getByText('novembro de 2026')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Aplicar alteração'}));expect(apply).toHaveBeenCalledTimes(1)})
 it('preserves the closing modal and error for retry',()=>{render(<CycleClosingModal open cycle={cycle} error="Falha ao ajustar." onClose={()=>{}} onPreview={()=>{}} onApply={()=>{}}/>);expect(screen.getByRole('dialog',{name:'Conferir mudança de fechamento'})).toBeTruthy();expect(screen.getByRole('alert').textContent).toBe('Falha ao ajustar.');expect((screen.getByLabelText('Fechamento efetivo') as HTMLInputElement).value).toBe('2026-09-25')})
})
