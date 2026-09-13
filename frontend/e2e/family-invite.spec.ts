import {test,expect} from '@playwright/test'

test('INVITE-01 landing clears token from browser history before inspection',async({page})=>{
 await page.route('**/api/v1/auth/me',route=>route.fulfill({status:401,json:{code:'unauthorized',message:'Entre para continuar.'}}))
 await page.route('**/api/v1/auth/invites/inspect',async route=>{
  expect(new URL(page.url()).search).toBe('')
  await route.fulfill({status:200,json:{status:'valid',family_name:'Família Silva',expires_at:'2026-09-20T10:00:00Z'}})
 })
 await page.goto('/invite?token=family.super-secret')
 await expect(page.getByRole('heading',{name:'Você foi convidado'})).toBeVisible()
 await expect(page.getByText('Família Silva')).toBeVisible()
 expect(new URL(page.url()).search).toBe('')
 expect(await page.content()).not.toContain('super-secret')
})
