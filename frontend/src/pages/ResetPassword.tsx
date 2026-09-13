import {useEffect,useState,type FormEvent} from 'react'
import {Layers,LockKeyhole} from 'lucide-react'
import {api} from '../api/client'

type State='validating'|'valid'|'invalid'|'completed'

function secureTokenFromLocation(){
 let meta=document.querySelector<HTMLMetaElement>('meta[name="referrer"]')
 if(!meta){meta=document.createElement('meta');meta.name='referrer';document.head.appendChild(meta)}
 meta.content='no-referrer'
 const token=new URLSearchParams(window.location.search).get('token')??''
 window.history.replaceState({},'',window.location.pathname)
 return token
}

export function ResetPassword({onBack}:{onBack?:()=>void}={}){
 const [token]=useState(secureTokenFromLocation)
 const [state,setState]=useState<State>('validating'),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 const back=()=>onBack?onBack():window.location.assign('/')
 useEffect(()=>{
  if(!token){setError('Link de redefinição incompleto. Solicite um novo link.');setState('invalid');return}
  api('/auth/password-reset/validate',{method:'POST',body:JSON.stringify({token})}).then(()=>setState('valid')).catch(caught=>{setError(caught instanceof Error?caught.message:'Este link não está mais disponível.');setState('invalid')})
 },[token])
 async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError('');try{await api('/auth/password-reset/complete',{method:'POST',body:JSON.stringify({token,password})});setPassword('');setState('completed')}catch(caught){setError(caught instanceof Error?caught.message:'Não foi possível redefinir a senha.')}finally{setBusy(false)}}
 return <main className="recovery-layout"><section className="recovery-card"><div className="brand"><Layers/><span>entre nós<span className="brand-dot">.</span></span></div><div className="icon-circle"><LockKeyhole/></div><span className="eyebrow">NOVA SENHA</span><h1>{state==='completed'?'Acesso protegido novamente.':'Crie uma nova senha'}</h1>{state==='validating'&&<p role="status">Validando link…</p>}{state==='valid'&&<><p>Use de 15 a 200 caracteres. Espaços e caracteres Unicode são aceitos.</p><form onSubmit={submit}><label>Nova senha<input type="password" autoComplete="new-password" minLength={15} maxLength={200} required value={password} onChange={event=>setPassword(event.target.value)}/></label>{error&&<div className="error" role="alert">{error}</div>}<button className="primary" disabled={busy}>{busy?'Redefinindo…':'Redefinir senha'}</button></form></>}{state==='invalid'&&<><div className="error" role="alert">{error}</div><a className="button-link" href="/forgot-password">Solicitar outro link</a></>}{state==='completed'&&<><div className="notice" role="status">Senha redefinida. Por segurança, todas as sessões anteriores foram encerradas.</div><button type="button" onClick={back}>Voltar para entrar</button></>}</section></main>
}
