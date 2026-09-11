import React from 'react'
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react'
import {afterEach,expect,it,vi} from 'vitest'
import {ScheduledExpenseForm} from './ScheduledExpenseForm'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn(),createOperation:vi.fn()}))
import {api,createOperation} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it.each(['rule','import'] as const)('ENTRY retains %s form after failed save and allows retry',async mode=>{
 vi.mocked(api).mockImplementation(async path=>path==='/cards'?[]:{installments:[{number:10,month:'2026-10-01',amount_cents:4351}]})
 const operation=vi.fn().mockRejectedValueOnce(new Error('Falha de conexão.')).mockResolvedValueOnce({id:'saved'})
 vi.mocked(createOperation).mockReturnValue(operation)
 const onSaved=vi.fn()
 render(<ScheduledExpenseForm auth={{user:{id:'u',name:'Douglas'},members:[{id:'u',name:'Douglas'}],family_id:'f'}} mode={mode} initialMonth="2026-10" onClose={()=>{}} onBack={()=>{}} onSaved={onSaved} feedback=""/>)
 fireEvent.change(screen.getByLabelText('Descrição'),{target:{value:'Despesa mantida'}})
 fireEvent.change(screen.getByLabelText('Valor da parcela ou conta (R$)'),{target:{value:'43.51'}})
 if(mode==='import'){
  fireEvent.change(screen.getByLabelText('Parcelas ainda abertas'),{target:{value:'10-12'}})
  fireEvent.submit(screen.getByRole('button',{name:'Conferir parcelas restantes'}).closest('form')!)
  await waitFor(()=>expect(screen.getByText('10/12 · outubro de 2026')).toBeTruthy())
  expect(createOperation).not.toHaveBeenCalled()
 }
 const button=()=>screen.getByRole('button',{name:mode==='rule'?'Salvar conta':'Salvar parcelas'})
 fireEvent.submit(button().closest('form')!)
 await waitFor(()=>expect(screen.getByRole('alert').textContent).toBe('Falha de conexão.'))
 expect((screen.getByLabelText('Descrição') as HTMLInputElement).value).toBe('Despesa mantida')
 expect((screen.getByLabelText('Valor da parcela ou conta (R$)') as HTMLInputElement).value).toBe('43.51')
 expect(onSaved).not.toHaveBeenCalled()
 fireEvent.submit(button().closest('form')!)
 await waitFor(()=>expect(onSaved).toHaveBeenCalledWith(false))
})
