import React from 'react'
import {render,screen,waitFor,cleanup} from '@testing-library/react'
import {it,expect,vi,afterEach} from 'vitest'
import {Commitment} from './Commitment'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn()}))
import {api} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('ADV-01 keeps original count separate from pending count',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>path==='/advances'?[]:{description:'Carro',original_count:48,pending_count:35,last_open_number:44,installments:[],imported:true})
 render(<Commitment id="car" onClose={()=>{}} onChanged={()=>{}}/>)
 await waitFor(()=>expect(screen.getByTestId('pending-count').textContent).toBe('35'))
 expect(screen.getByText('48 parcelas')).toBeTruthy()
 expect(screen.getByText('Última parcela em aberto: 44')).toBeTruthy()
})
