import {test,expect} from '@playwright/test'
import {login} from './helpers'
test('ADV-01 plan and cancel an original installment through UI',async({page})=>{
 await login(page)
 await page.evaluate(async()=>{const me=await(await fetch('/api/v1/auth/me')).json();const csrf=await(await fetch('/api/v1/auth/csrf')).json();await fetch('/api/v1/commitments/import',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf.csrf_token,'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({description:'Carro',buyer_id:me.user.id,first_month:'2026-10-01',original_count:48,numbers:[10,44],installment_cents:191900,shares:[{user_id:me.user.id,weight:1}]})})})
 // Fixture was inserted directly through the API; reload to fetch its persisted state.
 await page.reload()
 await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 await page.getByRole('button',{name:/Carro.*Parcela 10/}).first().click()
 await page.getByLabel('Selecionar parcela 44',{exact:true}).check()
 await page.getByLabel('Data prevista para antecipar',{exact:true}).fill('2026-10-05')
 await page.getByLabel('Valor final com desconto (R$)',{exact:true}).fill('1084')
 await page.getByRole('button',{name:'Conferir antecipação',exact:true}).click()
 await expect(page.getByText(/Desconto:.*835,00/)).toBeVisible()
 await page.getByRole('button',{name:'Planejar antecipação',exact:true}).click()
 await expect(page.getByText('Planejada',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Cancelar antecipação',exact:true}).click()
 await expect(page.getByRole('dialog',{name:'Cancelar antecipação?'})).toBeVisible()
 await page.getByRole('button',{name:'Confirmar cancelamento',exact:true}).click()
 await expect(page.getByText('Cancelada',{exact:true})).toBeVisible()
 await expect(page.getByTestId('pending-count')).toHaveText('2')
})
