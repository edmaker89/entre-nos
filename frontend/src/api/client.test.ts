import {afterEach,expect,it,vi} from 'vitest'
import {api,createOperation} from './client'
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
