import {test,expect} from '@playwright/test'

test('AUTH-RESET-01 request is generic and reachable from login',async({page})=>{
 await page.route('**/api/v1/auth/me',route=>route.fulfill({status:401,json:{code:'unauthorized',message:'Entre para continuar.'}}))
 await page.route('**/api/v1/auth/password-reset/request',async route=>{
  expect(route.request().method()).toBe('POST')
  expect(route.request().postDataJSON()).toEqual({email:'pessoa@example.com'})
  await route.fulfill({status:202,json:{message:'Se existir uma conta para este email, enviaremos as instruções de redefinição.'}})
 })
 await page.goto('/')
 await page.getByRole('link',{name:'Esqueci minha senha'}).click()
 await page.getByLabel('Email',{exact:true}).fill('pessoa@example.com')
 await page.getByRole('button',{name:'Enviar instruções',exact:true}).click()
 await expect(page.getByRole('status')).toContainText('Se existir uma conta')
})

test('AUTH-RESET-01 clears URL token and accepts Unicode password without leaking it',async({page})=>{
 await page.route('**/api/v1/auth/password-reset/validate',async route=>{
  expect(new URL(page.url()).search).toBe('')
  expect(route.request().postDataJSON()).toEqual({token:'super-secret'})
  await route.fulfill({status:200,json:{status:'valid'}})
 })
 await page.route('**/api/v1/auth/password-reset/complete',async route=>{
  expect(route.request().postDataJSON()).toEqual({token:'super-secret',password:'  senha Unicode longa 🙂  '})
  await route.fulfill({status:200,json:{status:'completed'}})
 })
 await page.goto('/reset-password?token=super-secret')
 expect(new URL(page.url()).search).toBe('')
 expect(await page.content()).not.toContain('super-secret')
 await page.getByLabel('Nova senha',{exact:true}).fill('  senha Unicode longa 🙂  ')
 await page.getByRole('button',{name:'Redefinir senha',exact:true}).click()
 await expect(page.getByRole('status')).toContainText('Senha redefinida')
 await page.getByRole('button',{name:'Voltar para entrar',exact:true}).click()
 await expect(page.getByRole('button',{name:'Entrar',exact:true})).toBeVisible()
})
