import React from 'react'
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react'
import {it,expect,vi,afterEach} from 'vitest'
import {CommitmentForm} from './CommitmentForm'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn(),createOperation:vi.fn()}))
import {api,createOperation} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('BUY-01 preview precedes save and failure preserves fields',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>path==='/cards'?[]:{installments:[{number:1,amount_cents:10000,month:'2026-10-01',needs_review:false}]})
 vi.mocked(createOperation).mockReturnValue(vi.fn().mockRejectedValue(new Error('Falha de conexão.')))
 render(<CommitmentForm auth={{user:{id:'u',name:'Douglas'},members:[{id:'u',name:'Douglas'}],family_id:'f'}} onClose={()=>{}} onSaved={()=>{}}/>)
 fireEvent.change(screen.getByLabelText('Descrição'),{target:{value:'Mercado'}})
 fireEvent.change(screen.getByLabelText('Valor total (R$)'),{target:{value:'100.00'}})
 fireEvent.submit(screen.getByRole('button',{name:'Conferir parcelas'}).closest('form')!)
 await waitFor(()=>expect(screen.getByRole('button',{name:'Salvar gasto'})).toBeTruthy())
 expect(createOperation).not.toHaveBeenCalled()
 fireEvent.click(screen.getByRole('button',{name:'Salvar gasto'}))
 await waitFor(()=>expect(screen.getByRole('alert').textContent).toBe('Falha de conexão.'))
 expect((screen.getByLabelText('Descrição') as HTMLInputElement).value).toBe('Mercado')
})
