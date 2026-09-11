import {useEffect,useState} from 'react'
import {api,createOperation,money,monthLabel} from '../api/client'
import {cents} from '../components/CommitmentForm'
export function RecurrenceManager({month,refresh,onChanged}:{month:string,refresh:number,onChanged:()=>void}){
 const [rules,setRules]=useState<any[]>([]),[error,setError]=useState('')
 const from=month
 async function load(){setRules(await api(`/recurrences?from_month=${from}-01&months=12`))}
 useEffect(()=>{load().catch(e=>setError(e.message))},[from,refresh])
 return <section style={{marginTop:28}}><h2>Contas recorrentes</h2><p>Ajuste valores mensais ou encerre as próximas cobranças.</p>{error&&<div role="alert" className="error">{error}</div>}
<div className="grid two">{rules.map(r=><section className="panel" key={r.id}><div className="row spread"><h3>{r.description}</h3><span className="badge">{r.variable?'Variável':'Fixa'}</span></div><p>{money(r.amount_cents)} · vence dia {r.due_day}</p>{r.end_month?<small>Encerrada a partir de {monthLabel(r.end_month.slice(0,7))}</small>:<button onClick={async()=>{const end=window.prompt('Encerrar a partir de qual mês? (AAAA-MM)',from);if(!end)return;try{await createOperation(`/recurrences/${r.id}/end`,'POST',{version:r.version,end_month:end+'-01'})();await load();onChanged()}catch(e){setError((e as Error).message)}}}>Encerrar recorrência</button>}<details style={{marginTop:14}}><summary>Valores por mês</summary>{r.occurrences.map((o:any)=><div className="row spread" key={o.id} style={{marginTop:8}}><small>{monthLabel(o.month.slice(0,7))} · {money(o.amount_cents)} {o.estimated?'(estimado)':''}</small><button onClick={async()=>{const value=window.prompt('Valor da conta (R$)',(o.amount_cents/100).toFixed(2));if(!value)return;try{await createOperation(`/occurrences/${o.id}`,'PATCH',{version:o.version,amount_cents:cents(value)})();await load();onChanged()}catch(e){setError((e as Error).message)}}}>Ajustar valor</button></div>)}</details></section>)}</div>{!rules.length&&<p>Aluguel, energia e internet podem entrar automaticamente no seu planejamento.</p>}</section>
}
