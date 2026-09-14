import {expect,test,type Page, type Route} from '@playwright/test'

const auth={user:{id:'douglas',name:'Douglas',email:'douglas@example.test',version:1},members:[{id:'douglas',name:'Douglas'},{id:'vanessa',name:'Vanessa'}],family_id:'family'}
const emptyMonth={month:'2026-10',current_month:'2026-10',current_remaining:0,items:[],people:[],family_total:0,totals:{expected:0,paid:0,remaining:0}}
const commitment={id:'purchase',version:3,description:'Notebook',category:'Trabalho',buyer_id:'douglas',card_id:null,purchased_at:'2026-09-12',total_cents:30000,original_count:3,pending_count:2,last_open_number:3,shares:[{user_id:'douglas',weight:30000}],installments:[
 {id:'part-1',number:1,month:'2026-10-01',original_month:'2026-10-01',amount_cents:10000,paid_at:'2026-10-10',shares:[{user_id:'douglas',weight:10000}]},
 {id:'part-2',number:2,month:'2026-11-01',original_month:'2026-11-01',amount_cents:10000,paid_at:null,shares:[{user_id:'douglas',weight:10000}]},
 {id:'part-3',number:3,month:'2026-12-01',original_month:'2026-12-01',amount_cents:10000,paid_at:null,shares:[{user_id:'douglas',weight:10000}]},
]}

type MockState={cards:any[];profileName:string}

function monthWithPurchase(){return {...emptyMonth,items:[{id:'part-2',kind:'installment',commitment_id:'purchase',description:'Notebook',number:2,original_count:3,version:3,paid_at:null,estimated:false,display_cents:10000,shares:[{user_id:'douglas',name:'Douglas',amount_cents:10000}]}],family_total:10000,people:[{id:'douglas',amount_cents:10000}],totals:{expected:10000,paid:0,remaining:10000}}}

async function authenticatedApp(page:Page,state:MockState={cards:[],profileName:'Douglas'}){
 await page.route('**/api/v1/**',route=>mockApi(route,state))
 await page.goto('/')
 await expect(page.getByRole('heading',{name:'Resumo',exact:true})).toBeVisible()
}

async function mockApi(route:Route,state:MockState){
 const request=route.request(),method=request.method(),path=new URL(request.url()).pathname.replace('/api/v1','')
 if(path==='/auth/me')return route.fulfill({json:{...auth,user:{...auth.user,name:state.profileName}}})
 if(path==='/auth/csrf')return route.fulfill({json:{csrf_token:'acceptance-csrf'}})
 if(path.startsWith('/months/'))return route.fulfill({json:path==='/months/default'?monthWithPurchase():monthWithPurchase()})
 if(path==='/commitments/purchase')return route.fulfill({json:commitment})
 if(path==='/advances')return route.fulfill({json:[]})
 if(path==='/commitments/purchase/responsibility-preview')return route.fulfill({json:{source_version:3,preview_hash:'transfer-hash',open_total_cents:20000,open_installment_count:2,months:['2026-11','2026-12'],planned_advances:[]}})
 if(path==='/commitments/purchase/edit-preview')return route.fulfill({json:{source_version:3,preview_hash:'edit-hash',before:{installments:commitment.installments},after:{installments:commitment.installments},affected_cycles:[],planned_advances:[]}})
 if(path==='/cards'&&method==='GET')return route.fulfill({json:state.cards})
 if(path==='/cards'&&method==='POST'){
  const body=request.postDataJSON()
  state.cards.push({...body,id:`card-${state.cards.length+1}`,version:1})
  return route.fulfill({json:state.cards.at(-1)})
 }
 if(path==='/family')return route.fulfill({json:{family:{id:'family',name:'Família Silva',code:'CASA2026',version:2},members:[{id:'douglas',name:'Douglas',role:'owner'},{id:'vanessa',name:'Vanessa',role:'member'}],invites:[],capabilities:{manage_family:true,manage_invites:true}}})
 if(path==='/family/invites')return route.fulfill({json:{id:'invite',link:'http://localhost:5173/invite?token=one-time',expires_at:'2026-09-21T12:00:00Z',one_time:true}})
 if(path==='/profile'&&method==='GET')return route.fulfill({json:{id:'douglas',name:state.profileName,email:'douglas@example.test',version:1,email_mutable:false}})
 if(path==='/profile'&&method==='PATCH'){
  state.profileName=request.postDataJSON().name
  return route.fulfill({json:{id:'douglas',name:state.profileName,email:'douglas@example.test',version:2,email_mutable:false}})
 }
 return route.fulfill({status:200,json:{}})
}

async function openCommitment(page:Page){
 await authenticatedApp(page)
 await page.locator('.desktop-only').getByText('Notebook',{exact:true}).click()
 await expect(page.getByRole('dialog',{name:'Notebook'})).toBeVisible()
}

test('EDIT-01 transfers only the two open installments to another family member',async({page})=>{
 await openCommitment(page)
 await page.getByRole('button',{name:'Transferir responsabilidade'}).click()
 const dialog=page.getByRole('dialog',{name:'Transferir responsabilidade'})
 await expect(dialog.getByText('Somente parcelas em aberto serão alteradas.')).toBeVisible()
 await expect(dialog.getByLabel('Transferir 100% para')).toHaveValue('vanessa')
 await dialog.getByRole('button',{name:'Conferir transferência'}).click()
 await expect(dialog.getByRole('region',{name:'Prévia da transferência'})).toContainText('2 parcelas abertas')
})

test('EDIT-02 edits a launch through preview and shared product modal',async({page})=>{
 await openCommitment(page)
 await page.getByRole('button',{name:'Editar lançamento'}).click()
 const dialog=page.getByRole('dialog',{name:'Editar lançamento'})
 await dialog.getByLabel('Descrição',{exact:true}).fill('Notebook do escritório')
 await dialog.getByRole('button',{name:'Conferir alterações'}).click()
 await expect(dialog.getByRole('region',{name:'Prévia da edição'})).toContainText('Antes e depois')
 await expect(dialog.getByRole('button',{name:'Salvar alterações'})).toBeVisible()
})

test('MODAL-01 keeps native dialogs unused, focus contained and four viewports overflow-free',async({page})=>{
 let nativeDialogs=0
 page.on('dialog',async dialog=>{nativeDialogs++;await dialog.dismiss()})
 await page.route('**/api/v1/**',route=>mockApi(route,{cards:[],profileName:'Douglas'}))
 for(const width of [360,390,768,1440]){
  await page.setViewportSize({width,height:800})
  await page.goto('/')
  await page.getByRole('button',{name:'Adicionar despesa',exact:true}).click()
  const dialog=page.getByRole('dialog',{name:'Adicionar despesa'})
  await expect(dialog).toBeVisible()
  expect(await dialog.evaluate(node=>node.contains(document.activeElement))).toBe(true)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
  await dialog.getByRole('button',{name:'Fechar'}).click()
 }
 expect(nativeDialogs).toBe(0)
})

test('FAMILY-01 exposes family code, owner, member and owner management actions',async({page})=>{
 await authenticatedApp(page)
 await page.getByRole('button',{name:/Minha família/}).click()
 await expect(page.getByRole('heading',{name:'Família Silva'})).toBeVisible()
 await expect(page.getByText('CASA2026')).toBeVisible()
 await expect(page.locator('.family-members').getByText('Douglas',{exact:true})).toBeVisible()
 await expect(page.locator('.family-members').getByText('Vanessa',{exact:true})).toBeVisible()
 await expect(page.getByRole('button',{name:'Gerar novo código'})).toBeVisible()
})

test('INVITE-01 creates a one-time link and opens WhatsApp only after user action',async({page})=>{
 await page.addInitScript(()=>{(window as any).__openedUrl='';window.open=((url?:string|URL)=>{(window as any).__openedUrl=String(url);return null}) as typeof window.open})
 await authenticatedApp(page)
 await page.getByRole('button',{name:/Minha família/}).click()
 await page.getByRole('button',{name:'Gerar convite'}).click()
 const dialog=page.getByRole('dialog',{name:'Convidar para Família Silva'})
 await expect(dialog.getByLabel('Link do convite')).toHaveValue(/token=one-time/)
 expect(await page.evaluate(()=>(window as any).__openedUrl)).toBe('')
 await dialog.getByRole('button',{name:'Enviar pelo WhatsApp'}).click()
 expect(await page.evaluate(()=>(window as any).__openedUrl)).toMatch(/^https:\/\/wa\.me\/\?text=/)
})

test('PROFILE-01 updates the visible user name while keeping login email read-only',async({page})=>{
 const state={cards:[],profileName:'Douglas'}
 await authenticatedApp(page,state)
 await page.getByRole('button',{name:'Abrir perfil de Douglas'}).click()
 const dialog=page.getByRole('dialog',{name:'Meu perfil'})
 await expect(dialog.getByLabel('Email de acesso')).toHaveAttribute('readonly','')
 await dialog.getByLabel('Nome',{exact:true}).fill('Douglas Silva')
 await dialog.getByRole('button',{name:'Salvar perfil'}).click()
 await expect(page.getByRole('button',{name:'Abrir perfil de Douglas Silva'})).toBeVisible()
})

test('AUTH-RESET-01 submits a generic recovery request without exposing account existence',async({page})=>{
 await page.route('**/api/v1/auth/me',route=>route.fulfill({status:401,json:{code:'unauthorized',message:'Entre para continuar.'}}))
 await page.route('**/api/v1/auth/password-reset/request',async route=>{
  expect(route.request().postDataJSON()).toEqual({email:'pessoa@example.test'})
  await route.fulfill({status:202,json:{message:'Se existir uma conta para este email, enviaremos as instruções de redefinição.'}})
 })
 await page.goto('/')
 await page.getByRole('link',{name:'Esqueci minha senha'}).click()
 await page.getByLabel('Email',{exact:true}).fill('pessoa@example.test')
 await page.getByRole('button',{name:'Enviar instruções'}).click()
 await expect(page.getByRole('status')).toContainText('Se existir uma conta')
})

test('CARD-UX-01 renders proportional compact grids with 1, 4 and 12 cards at approved viewports',async({page})=>{
 const state:MockState={cards:[],profileName:'Douglas'}
 await page.route('**/api/v1/**',route=>mockApi(route,state))
 for(const {width,count} of [{width:360,count:1},{width:390,count:4},{width:768,count:12},{width:1440,count:12}]){
  state.cards=Array.from({length:count},(_,index)=>({id:`card-${index}`,version:1,name:`Cartão ${index+1}`,institution_key:index%2?'neon':'nubank',institution:index%2?'Neon':'Nubank',network:'visa',last_four:String(index).padStart(4,'0'),holder_id:'douglas',closing_day:25,due_day:5}))
  await page.setViewportSize({width,height:900})
  await page.goto('/')
  await page.getByRole('button',{name:'Cartões',exact:true}).click()
  const cards=page.locator('.payment-card-v2')
  await expect(cards).toHaveCount(count)
  const box=await cards.first().boundingBox()
  expect(box).not.toBeNull()
  expect(box!.width).toBeLessThanOrEqual(340)
  expect(box!.width/box!.height).toBeCloseTo(85.6/53.98,1)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth)).toBe(true)
 }
})

test('CARD-CATALOG-01 searches Neon and supports a custom institution without sensitive fields',async({page})=>{
 const state:MockState={cards:[],profileName:'Douglas'}
 await authenticatedApp(page,state)
 await page.getByRole('button',{name:'Cartões',exact:true}).click()
 await page.getByRole('button',{name:'Novo cartão'}).click()
 await page.getByLabel('Nome do cartão').fill('Neon pessoal')
 await page.getByLabel('Buscar instituição').fill('Neon')
 await page.getByRole('button',{name:'Neon',exact:true}).click()
 await page.getByLabel('Final do cartão').fill('2026')
 await page.getByRole('button',{name:'Salvar cartão'}).click()
 await expect(page.getByRole('article',{name:'Cartão Neon pessoal'})).toContainText('Neon')
 await page.getByRole('button',{name:'Novo cartão'}).click()
 await page.getByRole('button',{name:'Outra instituição'}).click()
 await page.getByLabel('Nome do cartão').fill('Cooperativa')
 await page.getByLabel('Nome da instituição').fill('Cooperativa local')
 await expect(page.getByLabel(/CVV/i)).toHaveCount(0)
 await expect(page.getByLabel(/número completo/i)).toHaveCount(0)
 await page.getByRole('button',{name:'Salvar cartão'}).click()
 await expect(page.getByRole('article',{name:'Cartão Cooperativa'})).toContainText('Cooperativa local')
})
