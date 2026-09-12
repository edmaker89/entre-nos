import {afterEach,expect,it,vi} from 'vitest'
import {ApiError,api,createOperation} from './client'
afterEach(()=>vi.restoreAllMocks())
it('DATA-01 keeps the same key and body on retry',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch')
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({csrf_token:'csrf'})))
 fetch.mockRejectedValueOnce(new TypeError('network'))
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({id:'one'})))
 const save=createOperation('/cards','POST',{name:'Card'})
 await expect(save()).rejects.toThrow('conexão')
 expect(await save()).toEqual({id:'one'})
 const first=fetch.mock.calls[1][1]!,second=fetch.mock.calls[2][1]!
 expect(first.headers).toEqual(second.headers)
 expect(first.body).toBe(second.body)
 expect(first.credentials).toBe('same-origin')
})
it('FAM-01 propagates expired session without inventing a success',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({message:'Entre para continuar.'}),{status:401}))
 await expect(api('/auth/me')).rejects.toMatchObject({status:401,message:'Entre para continuar.'})
})
it('DATA AC04 reuses an unfinished operation across new save handlers',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch')
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({csrf_token:'csrf'})))
 await api('/auth/login',{method:'POST'})
 fetch.mockRejectedValueOnce(new TypeError('network'))
 await expect(createOperation('/recurrences','POST',{amount_cents:36000})()).rejects.toThrow('conexão')
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({id:'saved'})))
 expect(await createOperation('/recurrences','POST',{amount_cents:36000})()).toEqual({id:'saved'})
 const failed=fetch.mock.calls[1][1]!,retry=fetch.mock.calls[2][1]!
 expect(retry.headers).toEqual(failed.headers)
 expect(retry.body).toBe(failed.body)
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({id:'another'})))
 expect(await createOperation('/recurrences','POST',{amount_cents:36000})()).toEqual({id:'another'})
 expect(fetch.mock.calls[3][1]!.headers).not.toEqual(retry.headers)
})
it('DATA AC04 interrupted response is explained and keeps retry identity',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch')
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({csrf_token:'csrf'})))
 await api('/auth/login',{method:'POST'})
 fetch.mockResolvedValueOnce(new Response('',{status:502}))
 await expect(createOperation('/advances','POST',{amount_cents:108400})()).rejects.toMatchObject({status:502,message:'Não foi possível confirmar a resposta do servidor. Seus dados foram mantidos; tente novamente.'})
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({id:'a'})))
 expect(await createOperation('/advances','POST',{amount_cents:108400})()).toEqual({id:'a'})
 expect(fetch.mock.calls[1][1]!.headers).toEqual(fetch.mock.calls[2][1]!.headers)
})

it('EDIT-01 preserves every structured field from a 409 response',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({
  code:'preview_stale',message:'A prévia mudou.',fields:['source_version'],difference_cents:25,operation_id:'op-409'
 }),{status:409}))
 await expect(api('/commitments/one/responsibility-preview')).rejects.toMatchObject({
  status:409,code:'preview_stale',message:'A prévia mudou.',fields:['source_version'],difference_cents:25,operation_id:'op-409'
 })
})

it('EDIT-02 preserves validation fields and split difference from 422',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({
  code:'invalid_split',message:'Faltam centavos.',fields:['shares'],difference_cents:-2,operation_id:'op-422'
 }),{status:422}))
 const error=await api('/commitments/one/edit-preview').catch(value=>value)
 expect(error).toBeInstanceOf(ApiError)
 expect(error).toMatchObject({status:422,code:'invalid_split',fields:['shares'],difference_cents:-2,operation_id:'op-422'})
})

it('non-JSON errors preserve HTTP status and actionable fallback',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('<html>failure</html>',{status:503}))
 await expect(api('/cards')).rejects.toMatchObject({
  status:503,message:'Não foi possível confirmar a resposta do servidor. Seus dados foram mantidos; tente novamente.'
 })
})

it('network errors remain distinguishable with status zero',async()=>{
 vi.spyOn(globalThis,'fetch').mockRejectedValue(new TypeError('offline'))
 await expect(api('/cards')).rejects.toMatchObject({
  status:0,message:'Falha de conexão. Seus dados foram mantidos; tente salvar novamente.'
 })
})

it('401 preserves server metadata and announces session expiration',async()=>{
 const listener=vi.fn()
 window.addEventListener('session-expired',listener,{once:true})
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({
  code:'unauthorized',message:'Entre para continuar.',operation_id:'op-auth'
 }),{status:401}))
 await expect(api('/auth/me')).rejects.toMatchObject({status:401,code:'unauthorized',operation_id:'op-auth'})
 expect(listener).toHaveBeenCalledTimes(1)
})

it('server failures keep the same idempotency key for retry',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch')
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({csrf_token:'csrf'})))
 await api('/auth/login',{method:'POST'})
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({code:'database_unavailable',message:'Tente novamente.'}),{status:503}))
 const save=createOperation('/cards','POST',{name:'Azul'})
 await expect(save()).rejects.toMatchObject({status:503,code:'database_unavailable'})
 fetch.mockResolvedValueOnce(new Response(JSON.stringify({id:'card'})))
 await expect(save()).resolves.toEqual({id:'card'})
 expect(fetch.mock.calls[1][1]!.headers).toEqual(fetch.mock.calls[2][1]!.headers)
 expect(fetch.mock.calls[1][1]!.body).toBe(fetch.mock.calls[2][1]!.body)
})
