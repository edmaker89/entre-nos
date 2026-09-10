import {test,expect} from '@playwright/test'
import {login} from './helpers'
test('BUY-01 mobile purchase preview and save',async({page})=>{
 await page.setViewportSize({width:390,height:844});await login(page)
 await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 await page.getByRole('button',{name:'Adicionar gasto',exact:true}).click()
 await page.getByLabel('Descrição',{exact:true}).fill('Mercado da família')
 await page.getByLabel('Valor total (R$)',{exact:true}).fill('300')
 await page.getByLabel('Parcelas',{exact:true}).fill('3')
 await page.getByLabel('Primeira competência',{exact:true}).fill('2026-10')
 await page.getByRole('button',{name:'Conferir parcelas',exact:true}).click()
 await expect(page.getByText('1/3 · outubro de 2026',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Salvar gasto',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await expect(page.getByTestId('expected')).toContainText('100,00')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})
