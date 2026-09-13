import React from 'react'
import {cleanup,fireEvent,render,screen} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {CardFormModal,type CardDraft} from './CardFormModal'

const members=[{id:'douglas',name:'Douglas'},{id:'vanessa',name:'Vanessa'}]
const base:CardDraft={name:'',institution_key:'nubank',institution:'Nubank',network:null,last_four:null,holder_id:'douglas',closing_day:25,due_day:5}
const setup=(props:Partial<React.ComponentProps<typeof CardFormModal>>={})=>{
 const onSubmit=vi.fn()
 render(<CardFormModal open initial={base} members={members} onClose={vi.fn()} onSubmit={onSubmit} {...props}/>)
 return onSubmit
}
afterEach(cleanup)

describe('CARD-CATALOG-01 CardFormModal',()=>{
 it('offers the searchable institution catalog including Neon and Outra',()=>{
  setup();expect(screen.getByRole('button',{name:'Neon'})).toBeTruthy();expect(screen.getByRole('button',{name:'Outra instituição'})).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Buscar instituição'),{target:{value:'mercado'}})
  expect(screen.getByRole('button',{name:'Mercado Pago'})).toBeTruthy();expect(screen.queryByRole('button',{name:'Nubank'})).toBeNull()
 })
 it('finds an institution by alias',()=>{setup();fireEvent.change(screen.getByLabelText('Buscar instituição'),{target:{value:'roxinho'}});expect(screen.getByRole('button',{name:'Nubank'})).toBeTruthy()})
 it('changes the preview theme and institution when Neon is selected',()=>{setup();fireEvent.click(screen.getByRole('button',{name:'Neon'}));expect(screen.getByLabelText('Prévia do cartão').getAttribute('style')).toContain('rgb(0, 83, 107)');expect(screen.getByLabelText('Prévia do cartão').textContent).toContain('Neon')})
 it('requires a custom name for Outra and preserves the selected option',()=>{const submit=setup();fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Meu cartão'}});fireEvent.click(screen.getByRole('button',{name:'Outra instituição'}));fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));expect(screen.getByRole('alert').textContent).toContain('nome da instituição');expect(screen.getByLabelText('Nome da instituição')).toBeTruthy();expect(submit).not.toHaveBeenCalled()})
 it('submits a custom institution with stable other key',()=>{const submit=setup();fireEvent.click(screen.getByRole('button',{name:'Outra instituição'}));fireEvent.change(screen.getByLabelText('Nome da instituição'),{target:{value:'Cooperativa Local'}});fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Meu cartão'}});fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));expect(submit).toHaveBeenCalledWith(expect.objectContaining({institution_key:'other',institution:'Cooperativa Local',name:'Meu cartão'}))})
 it('submits optional network and exactly four final digits separately',()=>{const submit=setup();fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Compras'}});fireEvent.change(screen.getByLabelText('Bandeira'),{target:{value:'visa'}});fireEvent.change(screen.getByLabelText('Final do cartão'),{target:{value:'0042'}});fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));expect(submit).toHaveBeenCalledWith(expect.objectContaining({network:'visa',last_four:'0042'}))})
 it('rejects an invalid final while preserving every typed value',()=>{const submit=setup();fireEvent.change(screen.getByLabelText('Nome do cartão'),{target:{value:'Viagem'}});fireEvent.change(screen.getByLabelText('Final do cartão'),{target:{value:'12x4'}});fireEvent.click(screen.getByRole('button',{name:'Salvar cartão'}));expect(screen.getByRole('alert').textContent).toContain('4 dígitos');expect((screen.getByLabelText('Nome do cartão') as HTMLInputElement).value).toBe('Viagem');expect((screen.getByLabelText('Final do cartão') as HTMLInputElement).value).toBe('12x4');expect(submit).not.toHaveBeenCalled()})
 it('prefills edit data and uses the edit title',()=>{setup({initial:{...base,id:'card',version:3,name:'Viagem',institution_key:'neon',institution:'Neon',holder_id:'vanessa',network:'mastercard',last_four:'9876'}});expect(screen.getByRole('dialog',{name:'Editar cartão'})).toBeTruthy();expect((screen.getByLabelText('Nome do cartão') as HTMLInputElement).value).toBe('Viagem');expect((screen.getByLabelText('Titular') as HTMLSelectElement).value).toBe('vanessa');expect((screen.getByLabelText('Bandeira') as HTMLSelectElement).value).toBe('mastercard')})
 it('shows an API error without clearing fields',()=>{setup({error:'Não foi possível salvar.'});expect(screen.getByRole('alert').textContent).toBe('Não foi possível salvar.');expect((screen.getByLabelText('Nome do cartão') as HTMLInputElement).value).toBe('')})
 it('disables submit and cancel while saving',()=>{setup({busy:true});expect((screen.getByRole('button',{name:'Salvando…'}) as HTMLButtonElement).disabled).toBe(true);expect((screen.getByRole('button',{name:'Cancelar'}) as HTMLButtonElement).disabled).toBe(true);expect(screen.getByRole('dialog').getAttribute('aria-busy')).toBe('true')})
 it('offers every family member as holder',()=>{setup();expect(screen.getByRole('option',{name:'Douglas'})).toBeTruthy();expect(screen.getByRole('option',{name:'Vanessa'})).toBeTruthy()})
})
