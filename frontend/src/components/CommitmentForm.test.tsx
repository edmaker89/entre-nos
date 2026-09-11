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
it('SPLIT AC04 sends custom responsibility values and displays the difference',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>{if(path==='/cards')return [];throw new Error('Faltam R$ 10,00 na divisão entre responsáveis.')})
 render(<CommitmentForm auth={{user:{id:'d',name:'Douglas'},members:[{id:'d',name:'Douglas'},{id:'v',name:'Vanessa'}],family_id:'f'}} onClose={()=>{}} onSaved={()=>{}}/>)
 fireEvent.change(screen.getByLabelText('Descrição'),{target:{value:'Mercado'}})
 fireEvent.change(screen.getByLabelText('Valor total (R$)'),{target:{value:'100'}})
 fireEvent.change(screen.getByLabelText('Quem fica responsável'),{target:{value:'custom'}})
 fireEvent.change(screen.getByLabelText('Valor de Douglas (R$)'),{target:{value:'70'}})
 fireEvent.change(screen.getByLabelText('Valor de Vanessa (R$)'),{target:{value:'20'}})
 fireEvent.submit(screen.getByRole('button',{name:'Conferir parcelas'}).closest('form')!)
 await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Faltam R$ 10,00'))
 const body=JSON.parse(vi.mocked(api).mock.calls.find(([path])=>path==='/commitments/preview')![1]!.body as string)
 expect(body.shares).toEqual([{user_id:'d',weight:7000},{user_id:'v',weight:2000}])
 expect((screen.getByLabelText('Valor de Douglas (R$)') as HTMLInputElement).value).toBe('70')
})
