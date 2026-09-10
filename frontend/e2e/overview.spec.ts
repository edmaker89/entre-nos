import {test,expect} from '@playwright/test'
import {login} from './helpers'
for(const width of [360,390,768,1440])test(`MONTH-01 dashboard at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900})
 await login(page)
 await expect(page.getByTestId('expected')).toContainText('0,00')
 await page.getByLabel('Competência',{exact:true}).fill('2026-10')
 await expect(page.getByLabel('Competência',{exact:true})).toHaveValue('2026-10')
 await page.getByRole('button',{name:'Próximo mês',exact:true}).click()
 await expect(page.getByLabel('Competência',{exact:true})).toHaveValue('2026-11')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})
test('MONTH and FAM preserve chosen month across navigation and allow mobile logout',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 await login(page)
 await page.getByLabel('Competência',{exact:true}).fill('2027-02')
 await page.getByRole('button',{name:'Cartões',exact:true}).click()
 await page.getByRole('button',{name:'Resumo',exact:true}).click()
 await expect(page.getByLabel('Competência',{exact:true})).toHaveValue('2027-02')
 await page.getByRole('button',{name:'Sair',exact:true}).click()
 await expect(page.getByRole('button',{name:'Entrar',exact:true})).toBeVisible()
})
