import React from 'react'
import {render,screen,waitFor,cleanup} from '@testing-library/react'
import {afterEach,it,expect,vi} from 'vitest'
import {Overview} from './Overview'
vi.mock('../api/client',async()=>{const actual=await vi.importActual('../api/client');return {...actual,api:vi.fn()}})
import {api} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('MONTH-01 renders exact expected paid and remaining totals',async()=>{
 vi.mocked(api).mockResolvedValue({month:'2026-10',current_month:'2026-10',current_remaining:5000,items:[],people:[],family_total:15000,totals:{expected:15000,paid:10000,remaining:5000}})
 render(<Overview auth={{user:{id:'d',name:'Douglas'},members:[],family_id:'f'}} onOpen={()=>{}} refresh={0}/>)
 await waitFor(()=>expect(screen.getByTestId('expected').textContent).toContain('150,00'))
 expect(screen.getByTestId('paid').textContent).toContain('100,00')
 expect(screen.getByTestId('remaining').textContent).toContain('50,00')
})
