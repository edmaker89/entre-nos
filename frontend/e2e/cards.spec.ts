import {test,expect} from '@playwright/test'
import {login} from './helpers'
test('CARD-01 create a card with its holder and closing dates',async({page})=>{
 await login(page);await page.getByRole('button',{name:'Cartões',exact:true}).click()
 await page.getByRole('button',{name:'Novo cartão',exact:true}).click()
 await page.getByLabel('Nome do cartão',{exact:true}).fill('Santander Casa')
 await page.getByLabel('Buscar instituição',{exact:true}).fill('Santander')
 await page.getByRole('button',{name:'Santander',exact:true}).click()
 await page.getByRole('combobox',{name:'Bandeira',exact:true}).selectOption('visa')
 await page.getByLabel('Final do cartão',{exact:true}).fill('0042')
 await page.getByLabel('Dia do fechamento',{exact:true}).fill('25')
 await page.getByLabel('Dia do vencimento',{exact:true}).fill('5')
 await page.getByRole('button',{name:'Salvar cartão',exact:true}).click()
 await expect(page.getByRole('article',{name:'Cartão Santander Casa',exact:true})).toContainText('•••• 0042')
 await page.getByRole('button',{name:'Ver faturas de Santander Casa',exact:true}).click()
 await expect(page.getByText('As faturas aparecerão quando você registrar uma compra neste cartão.')).toBeVisible()
})
