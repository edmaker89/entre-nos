import {execFileSync} from 'node:child_process'
import {randomUUID} from 'node:crypto'
import {type Page,expect} from '@playwright/test'
export async function login(page:Page){
 const email=`${randomUUID()}@browser.test`,password='browser-test-password'
 execFileSync('../backend/.venv/bin/python',['../frontend/e2e/provision.py',email,password],{cwd:'../backend',env:{...process.env,PYTHONPATH:'.'}})
 await page.goto('/')
 await page.getByLabel('Email',{exact:true}).fill(email)
 await page.getByLabel('Senha',{exact:true}).fill(password)
 await page.getByRole('button',{name:'Entrar',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Resumo',exact:true})).toBeVisible()
 return {email,password}
}
