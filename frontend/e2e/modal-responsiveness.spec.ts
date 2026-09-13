import {test,expect} from '@playwright/test'

for(const width of [360,390,768,1440]){
 test(`shared modal fits ${width}px without horizontal overflow`,async({page})=>{
  await page.setViewportSize({width,height:800})
  await page.route('**/api/v1/**',async route=>{
   const path=new URL(route.request().url()).pathname
   const body=path.endsWith('/auth/me')?{user:{id:'u',name:'Douglas'},members:[{id:'u',name:'Douglas'}],family_id:'f'}:path.includes('/months/')?{month:'2026-10',current_month:'2026-10',current_remaining:0,items:[],people:[],family_total:0,totals:{expected:0,paid:0,remaining:0}}:[]
   await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(body)})
  })
  await page.goto('/')
  await page.getByRole('button',{name:/Adicionar despesa/}).click()
  const dialog=page.getByRole('dialog',{name:'Adicionar despesa'})
  await expect(dialog).toBeVisible()
  const box=await dialog.boundingBox()
  expect(box).not.toBeNull()
  expect(box!.x).toBeGreaterThanOrEqual(0)
  expect(box!.x+box!.width).toBeLessThanOrEqual(width)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
  await expect(page.locator('.dialog-backdrop')).toHaveCount(0)
 })
}
