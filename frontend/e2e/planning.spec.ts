import {test,expect} from '@playwright/test'
import {login} from './helpers'
test('MIG-01 bring remaining parcels with preview',async({page})=>{
 await login(page);await page.getByRole('button',{name:'Planejamento',exact:true}).click()
 await page.getByRole('button',{name:'Adicionar despesa',exact:true}).click()
 await page.getByRole('button',{name:/Parcelas em andamento Uma compra/}).click()
 await page.getByLabel('Descrição',{exact:true}).fill('Panelas')
 await page.getByLabel('Valor da parcela ou conta (R$)',{exact:true}).fill('43.51')
 await page.getByLabel('Competência inicial',{exact:true}).fill('2026-10')
 await page.getByLabel('Total original de parcelas',{exact:true}).fill('12')
 await page.getByLabel('Parcelas ainda abertas',{exact:true}).fill('10-12')
 await page.getByRole('button',{name:'Conferir parcelas restantes',exact:true}).click()
 await expect(page.getByText('10/12 · outubro de 2026',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Salvar parcelas',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await page.getByLabel('Início da projeção',{exact:true}).fill('2026-10')
 await expect(page.getByRole('cell',{name:'R$ 43,51',exact:true})).toHaveCount(3)
})
