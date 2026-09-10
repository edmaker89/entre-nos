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
