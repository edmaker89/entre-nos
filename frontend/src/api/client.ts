let csrf:string|undefined
const pendingOperations=new Map<string,string>()
export class ApiError extends Error {constructor(message:string,public status:number){super(message)}}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T>{
 const method=options.method??'GET'
 if(method!=='GET'&&!csrf&&path!=='/auth/login'){
  csrf=(await api<{csrf_token:string}>('/auth/csrf')).csrf_token
 }
 let response:Response
 try {response=await fetch('/api/v1'+path,{...options,credentials:'same-origin',headers:{'Content-Type':'application/json',...(csrf?{'X-CSRF-Token':csrf}:{}),...options.headers}})}
 catch {throw new ApiError('Falha de conexão. Seus dados foram mantidos; tente salvar novamente.',0)}
 const data=await response.json()
 if(!response.ok){if(response.status===401){csrf=undefined;window.dispatchEvent(new Event('session-expired'))}throw new ApiError(data.message??'Não foi possível concluir.',response.status)}
 if(path==='/auth/login')csrf=data.csrf_token
 if(path==='/auth/logout'){csrf=undefined;pendingOperations.clear()}
 return data
}
export function createOperation<T=any>(path:string,method:string,body?:unknown){
 const serialized=body===undefined?undefined:JSON.stringify(body)
 const identity=JSON.stringify([path,method,serialized])
 const key=pendingOperations.get(identity)??crypto.randomUUID()
 pendingOperations.set(identity,key)
 return async()=>{
  try{
   const result=await api<T>(path,{method,headers:{'Idempotency-Key':key},...(serialized!==undefined?{body:serialized}:{})})
   if(pendingOperations.get(identity)===key)pendingOperations.delete(identity)
   return result
  }catch(error){
   if(error instanceof ApiError&&error.status>=400&&error.status<500&&pendingOperations.get(identity)===key)pendingOperations.delete(identity)
   throw error
  }
 }
}
export const money=(cents:number)=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(cents/100)
export const monthLabel=(month:string)=>new Intl.DateTimeFormat('pt-BR',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(month+'-01T12:00:00Z'))
export const today=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())
