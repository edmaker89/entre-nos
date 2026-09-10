import React from 'react'
import {render,screen,waitFor,cleanup} from '@testing-library/react'
import {it,expect,vi,afterEach} from 'vitest'
import {Planning} from './Planning'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn()}))
import {api} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('MONTH-01 identifies estimates in projection',async()=>{
 vi.mocked(api).mockImplementation(async(path)=>path.startsWith('/forecast')?[{month:'2026-10',totals:{expected:36000},items:[{estimated:true}]}]:[])
 render(<Planning auth={{user:{id:'u',name:'Douglas'},members:[],family_id:'f'}} onChanged={()=>{}}/>)
 await waitFor(()=>expect(screen.getByText('Inclui estimativas')).toBeTruthy())
 expect(screen.getByText(/360,00/)).toBeTruthy()
})
