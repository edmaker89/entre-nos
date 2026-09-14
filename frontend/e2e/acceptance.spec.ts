import {test,expect,type Page} from '@playwright/test'
import {login} from './helpers'

async function seed(page:Page,path:string,body:any){return page.evaluate(async({path,body})=>{
 const me=await(await fetch('/api/v1/auth/me')).json()
 const csrf=await(await fetch('/api/v1/auth/csrf')).json()
 const identity=path.startsWith('/commitments')?{buyer_id:me.user.id,shares:[{user_id:me.user.id,weight:body.total_cents??1}]}:path==='/cards'?{holder_id:me.user.id}:{}
 const response=await fetch('/api/v1'+path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf.csrf_token,'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({...body,...identity})})
 if(!response.ok)throw new Error(await response.text())
 return response.json()
},{path,body})}

for(const width of [360,390,768,1440])test(`BUY MONTH complete preview and touch targets at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});await login(page)
 await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 for(const button of await page.getByRole('button').all()){
  if(await button.isVisible()){const box=await button.boundingBox();expect(box!.width).toBeGreaterThanOrEqual(44);expect(box!.height).toBeGreaterThanOrEqual(44)}
 }
 await page.getByRole('button',{name:'Adicionar despesa',exact:true}).click()
 await page.getByRole('button',{name:/Compra ou despesa Uma compra nova/}).click()
 await page.getByLabel('Descrição',{exact:true}).fill('Compra com descrição longa para conferir no celular')
 await page.getByLabel('Valor total (R$)',{exact:true}).fill('300')
 await page.getByLabel('Parcelas',{exact:true}).fill('3')
 await page.getByLabel('Primeira competência',{exact:true}).fill('2026-10')
 await page.getByRole('button',{name:'Conferir parcelas',exact:true}).click()
 for(const text of ['1/3 · outubro de 2026','2/3 · novembro de 2026','3/3 · dezembro de 2026'])await expect(page.getByText(text,{exact:true})).toBeVisible()
 await expect(page.getByRole('dialog').getByText(/100,00/)).toHaveCount(3)
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.getByRole('button',{name:'Salvar gasto',exact:true}).click()
 await expect(page.getByTestId('expected')).toContainText('100,00')
 await expect(page.getByLabel('Competência',{exact:true})).toHaveValue('2026-10')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})

test('DATA response lost after card commit retries without duplication',async({page})=>{
 await login(page)
 await page.getByRole('button',{name:'Cartões',exact:true}).click()
 await page.getByRole('button',{name:'Novo cartão',exact:true}).click()
 await page.getByLabel('Nome do cartão').fill('Cartão sem duplicação')
 await page.getByRole('button',{name:'Outra instituição',exact:true}).click()
 await page.getByLabel('Nome da instituição',{exact:true}).fill('Banco')
 let lost=false;const keys:string[]=[]
 await page.route('**/api/v1/cards',async route=>{
  if(route.request().method()!=='POST')return route.continue()
  keys.push(route.request().headers()['idempotency-key'])
  const response=await route.fetch()
  expect(response.status()).toBe(200)
  if(!lost){lost=true;await route.abort('failed')}else await route.fulfill({response})
 })
 await page.getByRole('button',{name:'Salvar cartão',exact:true}).click()
 await expect(page.getByRole('dialog').getByRole('alert')).toContainText('Falha de conexão')
 await expect(page.getByLabel('Nome do cartão')).toHaveValue('Cartão sem duplicação')
 await page.getByRole('button',{name:'Salvar cartão',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 expect(keys).toHaveLength(2);expect(keys[1]).toBe(keys[0])
 expect(await page.evaluate(async()=>(await(await fetch('/api/v1/cards')).json()).length)).toBe(1)
})

test('ADV persisted history includes original date amount discount and linked lines',async({page})=>{
 await page.setViewportSize({width:390,height:900});await login(page)
 const c=await seed(page,'/commitments/import',{description:'Carro',first_month:'2026-10-01',original_count:48,numbers:[10,44],installment_cents:191900})
 await seed(page,'/advances',{commitment_id:c.id,version:c.version,installment_ids:[c.installments[1].id],planned_date:'2026-10-05',amount_cents:108400})
 await page.reload();await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 await expect(page.getByTestId('expected')).toContainText('3.003,00')
 await expect(page.locator('.mobile-only').getByText('Carro',{exact:true})).toHaveCount(2)
 await expect(page.locator('.mobile-only').getByText('Antecipação · parcela 44/48',{exact:true})).toBeVisible()
 await page.locator('.mobile-only').getByRole('button',{name:/Carro.*10\/48/}).click()
 await expect(page.getByText(/Original:.*1.919,00.*Desconto:.*835,00/)).toBeVisible()
 await expect(page.getByText(/Original: agosto de 2029/)).toBeVisible()
 await expect(page.getByTestId('pending-count')).toHaveText('2')
})

test('MONTH pending warning persists and returns to current month',async({page})=>{
 await login(page)
 const current=await page.evaluate(async()=>(await(await fetch('/api/v1/months/default')).json()).current_month)
 await seed(page,'/commitments',{description:'Pendente atual',purchased_at:current+'-01',first_month:current+'-01',total_cents:15000,count:1})
 await page.reload()
 const next=new Date(current+'-01T12:00:00Z');next.setUTCMonth(next.getUTCMonth()+1)
 await page.getByLabel('Competência',{exact:true}).fill(next.toISOString().slice(0,7))
 await expect(page.locator('.notice')).toContainText('150,00')
 await expect(page.locator('.month-control .badge')).toHaveText('Próximo mês')
 await page.getByRole('button',{name:'Cartões',exact:true}).click()
 await page.getByRole('button',{name:'Resumo',exact:true}).click()
 await expect(page.locator('.notice')).toContainText('150,00')
 await page.getByRole('button',{name:'Ver mês atual'}).click()
 await expect(page.getByLabel('Competência',{exact:true})).toHaveValue(current)
 await expect(page.locator('.month-control .badge')).toHaveText('Mês atual')
})

test('BUY closing-day review and MONTH final installment in twelve-month projection',async({page})=>{
 await login(page)
 const card=await seed(page,'/cards',{name:'Cartão',institution:'Banco',closing_day:25,due_day:5})
 await seed(page,'/commitments',{description:'Compra no fechamento',card_id:card.id,purchased_at:'2026-09-25',total_cents:30000,count:3})
 await page.reload();await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 await expect(page.locator('.desktop-only').getByText(/Parcela 1\/3 · Conferir fatura/)).toBeVisible()
 await page.getByRole('button',{name:'Planejamento',exact:true}).click()
 await page.getByLabel('Início da projeção').fill('2026-10')
 await expect(page.locator('tbody tr')).toHaveCount(12)
 await expect(page.getByRole('row').filter({hasText:'dezembro de 2026'})).toContainText('Compra no fechamento · 3/3')
 await expect(page.getByRole('row').filter({hasText:'janeiro de 2027'})).toContainText('0,00')
})
