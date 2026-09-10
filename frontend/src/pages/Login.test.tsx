import React from 'react'
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react'
import {afterEach,it,expect,vi} from 'vitest'
import {Login} from './Login'
vi.mock('../api/client',()=>({api:vi.fn()}))
import {api} from '../api/client'
afterEach(()=>{cleanup();vi.clearAllMocks()})
it('AUTH-01 login failure preserves email and explains error',async()=>{
 vi.mocked(api).mockRejectedValue(new Error('Email ou senha incorretos.'))
 render(<Login onLogin={()=>{}}/> )
 fireEvent.change(screen.getByLabelText('Email'),{target:{value:'douglas@test.local'}})
 fireEvent.change(screen.getByLabelText('Senha'),{target:{value:'wrong'}})
 fireEvent.click(screen.getByRole('button',{name:'Entrar'}))
 await waitFor(()=>expect(screen.getByRole('alert').textContent).toBe('Email ou senha incorretos.'))
 expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('douglas@test.local')
})
