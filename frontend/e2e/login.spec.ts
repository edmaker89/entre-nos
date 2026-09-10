import {test,expect} from '@playwright/test'
import {login} from './helpers'
test('AUTH-01 login persists across reload and logout revokes session',async({page})=>{
 await login(page)
 await page.reload()
 await expect(page.getByRole('heading',{name:'Resumo',exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Sair',exact:true}).click()
 await expect(page.getByRole('button',{name:'Entrar',exact:true})).toBeVisible()
 expect(await page.evaluate(()=>Object.keys(localStorage))).toEqual([])
})
