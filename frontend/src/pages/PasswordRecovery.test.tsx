import React from 'react'
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react'
import {afterEach,describe,expect,it,vi} from 'vitest'
import {api} from '../api/client'
import {ForgotPassword} from './ForgotPassword'
import {Login} from './Login'
import {ResetPassword} from './ResetPassword'

vi.mock('../api/client',()=>({api:vi.fn()}))

afterEach(()=>{
 cleanup()
 vi.clearAllMocks()
 window.history.replaceState({},'', '/')
 document.querySelector('meta[name="referrer"]')?.remove()
})

describe('AUTH-RESET-01 request',()=>{
 it('login exposes a direct password recovery entry point',()=>{
  render(<Login onLogin={()=>{}}/>)
  expect(screen.getByRole('link',{name:'Esqueci minha senha'}).getAttribute('href')).toBe('/forgot-password')
 })

 it('submits the email and always shows the generic confirmation',async()=>{
  vi.mocked(api).mockResolvedValue({message:'Se existir uma conta para este email, enviaremos as instruções de redefinição.'})
  render(<ForgotPassword onBack={()=>{}}/>)
  fireEvent.change(screen.getByLabelText('Email'),{target:{value:'douglas@example.com'}})
  fireEvent.click(screen.getByRole('button',{name:'Enviar instruções'}))
  expect((await screen.findByRole('status')).textContent).toContain('Se existir uma conta')
  expect(api).toHaveBeenCalledWith('/auth/password-reset/request',{
   method:'POST',body:JSON.stringify({email:'douglas@example.com'})
  })
 })

 it('preserves the submitted email when the network fails',async()=>{
  vi.mocked(api).mockRejectedValue(new Error('Falha de conexão. Tente novamente.'))
  render(<ForgotPassword onBack={()=>{}}/>)
  fireEvent.change(screen.getByLabelText('Email'),{target:{value:'vanessa@example.com'}})
  fireEvent.click(screen.getByRole('button',{name:'Enviar instruções'}))
  expect((await screen.findByRole('alert')).textContent).toContain('Falha de conexão')
  expect((screen.getByLabelText('Email') as HTMLInputElement).value).toBe('vanessa@example.com')
 })

 it('returns to login only after an explicit action',()=>{
  const back=vi.fn()
  render(<ForgotPassword onBack={back}/>)
  expect(back).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button',{name:'Voltar para entrar'}))
  expect(back).toHaveBeenCalledTimes(1)
 })
})

describe('AUTH-RESET-01 completion',()=>{
 it('removes the raw token before POST validation and sets no-referrer',async()=>{
  window.history.replaceState({},'', '/reset-password?token=raw-secret')
  vi.mocked(api).mockImplementation(async(path,options)=>{
   expect(window.location.href).not.toContain('raw-secret')
   expect(document.querySelector('meta[name="referrer"]')?.getAttribute('content')).toBe('no-referrer')
   expect(path).toBe('/auth/password-reset/validate')
   expect(options?.body).toBe(JSON.stringify({token:'raw-secret'}))
   return {status:'valid'}
  })
  render(<ResetPassword onBack={()=>{}}/>)
  expect(await screen.findByLabelText('Nova senha')).toBeTruthy()
  expect(window.location.pathname).toBe('/reset-password')
  expect(window.location.search).toBe('')
  expect(document.body.textContent).not.toContain('raw-secret')
 })

 it('accepts and sends a 15-character Unicode password with surrounding spaces',async()=>{
  window.history.replaceState({},'', '/reset-password?token=secret')
  vi.mocked(api).mockResolvedValueOnce({status:'valid'}).mockResolvedValueOnce({status:'completed'})
  render(<ResetPassword onBack={()=>{}}/>)
  const field=await screen.findByLabelText('Nova senha')
  const password='  senha Unicode 🙂  '
  fireEvent.change(field,{target:{value:password}})
  fireEvent.click(screen.getByRole('button',{name:'Redefinir senha'}))
  await waitFor(()=>expect(api).toHaveBeenLastCalledWith('/auth/password-reset/complete',{
   method:'POST',body:JSON.stringify({token:'secret',password})
  }))
  expect((await screen.findByRole('status')).textContent).toContain('Senha redefinida')
 })

 it('preserves the new password and displays a completion error',async()=>{
  window.history.replaceState({},'', '/reset-password?token=secret')
  vi.mocked(api).mockResolvedValueOnce({status:'valid'}).mockRejectedValueOnce(new Error('A nova senha deve ser diferente.'))
  render(<ResetPassword onBack={()=>{}}/>)
  const field=await screen.findByLabelText('Nova senha')
  fireEvent.change(field,{target:{value:'senha longa preservada'}})
  fireEvent.click(screen.getByRole('button',{name:'Redefinir senha'}))
  expect((await screen.findByRole('alert')).textContent).toContain('deve ser diferente')
  expect((field as HTMLInputElement).value).toBe('senha longa preservada')
 })

 it('normalizes invalid validation and offers a new request',async()=>{
  window.history.replaceState({},'', '/reset-password?token=expired')
  vi.mocked(api).mockRejectedValue(new Error('Este link expirou ou não está mais disponível. Solicite uma nova redefinição.'))
  render(<ResetPassword onBack={()=>{}}/>)
  expect((await screen.findByRole('alert')).textContent).toContain('Solicite uma nova redefinição')
  expect(screen.getByRole('link',{name:'Solicitar outro link'}).getAttribute('href')).toBe('/forgot-password')
  expect(screen.queryByLabelText('Nova senha')).toBeNull()
 })

 it('does not call the API when the URL has no token',async()=>{
  window.history.replaceState({},'', '/reset-password')
  render(<ResetPassword onBack={()=>{}}/>)
  expect((await screen.findByRole('alert')).textContent).toContain('Link de redefinição incompleto')
  expect(api).not.toHaveBeenCalled()
 })

 it('returns to login after success only when requested',async()=>{
  window.history.replaceState({},'', '/reset-password?token=secret')
  vi.mocked(api).mockResolvedValueOnce({status:'valid'}).mockResolvedValueOnce({status:'completed'})
  const back=vi.fn()
  render(<ResetPassword onBack={back}/>)
  fireEvent.change(await screen.findByLabelText('Nova senha'),{target:{value:'uma senha nova válida'}})
  fireEvent.click(screen.getByRole('button',{name:'Redefinir senha'}))
  const button=await screen.findByRole('button',{name:'Voltar para entrar'})
  expect(back).not.toHaveBeenCalled()
  fireEvent.click(button)
  expect(back).toHaveBeenCalledTimes(1)
 })
})
