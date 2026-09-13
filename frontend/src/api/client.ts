let csrf:string|undefined
const pendingOperations=new Map<string,string>()
const publicMutations=new Set(['/auth/login','/auth/invites/inspect','/auth/invites/register'])
type ApiErrorDetails={code?:string;fields?:string[];difference_cents?:number;operation_id?:string}
export class ApiError extends Error {
 constructor(message:string,public status:number,details:ApiErrorDetails={}){
  super(message)
  this.name='ApiError'
  Object.assign(this,details)
 }
 declare code?:string
 declare fields?:string[]
 declare difference_cents?:number
 declare operation_id?:string
}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T>{
 const method=options.method??'GET'
 if(method!=='GET'&&!csrf&&!publicMutations.has(path)){
  csrf=(await api<{csrf_token:string}>('/auth/csrf')).csrf_token
 }
 let response:Response
 try {response=await fetch('/api/v1'+path,{...options,credentials:'same-origin',headers:{'Content-Type':'application/json',...(csrf?{'X-CSRF-Token':csrf}:{}),...options.headers}})}
 catch {throw new ApiError('Falha de conexão. Seus dados foram mantidos; tente salvar novamente.',0)}
 let data:any
 try{data=await response.json()}
 catch{throw new ApiError('Não foi possível confirmar a resposta do servidor. Seus dados foram mantidos; tente novamente.',response.status)}
 if(!response.ok){if(response.status===401){csrf=undefined;window.dispatchEvent(new Event('session-expired'))}throw new ApiError(data.message??'Não foi possível concluir.',response.status,{code:data.code,fields:data.fields,difference_cents:data.difference_cents,operation_id:data.operation_id})}
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
