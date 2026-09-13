import {useState,type FormEvent} from 'react'
import {Layers,Mail} from 'lucide-react'
import {api} from '../api/client'

const GENERIC='Se existir uma conta para este email, enviaremos as instruções de redefinição.'

export function ForgotPassword({onBack}:{onBack?:()=>void}={}){
 const [email,setEmail]=useState(''),[message,setMessage]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 const back=()=>onBack?onBack():window.location.assign('/')
 async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError('');try{const result=await api<{message:string}>('/auth/password-reset/request',{method:'POST',body:JSON.stringify({email})});setMessage(result.message||GENERIC)}catch(caught){setError(caught instanceof Error?caught.message:'Não foi possível solicitar a redefinição.')}finally{setBusy(false)}}
 return <main className="recovery-layout"><section className="recovery-card"><div className="brand"><Layers/><span>entre nós<span className="brand-dot">.</span></span></div><div className="icon-circle"><Mail/></div><span className="eyebrow">RECUPERAÇÃO DE ACESSO</span><h1>Esqueceu sua senha?</h1><p>Informe seu email de acesso. Se a conta existir, enviaremos um link válido por 15 minutos.</p>{message?<><div className="notice" role="status">{message}</div><button type="button" onClick={back}>Voltar para entrar</button></>:<form onSubmit={submit}><label>Email<input type="email" autoComplete="email" required value={email} onChange={event=>setEmail(event.target.value)}/></label>{error&&<div className="error" role="alert">{error}</div>}<button className="primary" disabled={busy}>{busy?'Enviando…':'Enviar instruções'}</button><button type="button" onClick={back}>Voltar para entrar</button></form>}</section></main>
}
