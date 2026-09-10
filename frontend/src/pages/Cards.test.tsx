import React from 'react'
import {render,screen,waitFor,cleanup} from '@testing-library/react'
import {it,expect,vi,afterEach} from 'vitest'
import {Cards} from './Cards'
vi.mock('../api/client',async()=>({...await vi.importActual('../api/client'),api:vi.fn()}))
import {api} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('CARD-01 shows holder and configured cycle days',async()=>{
 vi.mocked(api).mockResolvedValue([{id:'c',name:'Santander',institution:'Banco',holder_id:'u',closing_day:25,due_day:5}])
 render(<Cards auth={{user:{id:'u',name:'Douglas'},members:[{id:'u',name:'Douglas'}],family_id:'f'}}/>)
 await waitFor(()=>expect(screen.getByText('Douglas')).toBeTruthy())
 expect(screen.getByText('25')).toBeTruthy();expect(screen.getByText('5')).toBeTruthy()
})
