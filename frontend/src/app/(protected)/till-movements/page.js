"use client";

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import OwnerGuard from '@/components/auth/owner-guard';
import PendingSaveNotice from '@/components/orders/pending-save-notice';
import usePendingSave from '@/components/orders/use-pending-save';
import { useAuth } from '@/context/auth-context';
import { formatKes, nairobiToday } from '@/lib/report-tools';
import { formatNairobiDateTime } from '@/lib/format-nairobi';
import { readRecordId } from '@/lib/record-id';
import { getUserMessage } from '@/lib/user-messages';
import { MOVEMENT_FIELDS, MOVEMENT_KINDS, movementBody, pendingMovementValues, isBusinessDate } from '@/lib/daily-close-tools';

const INPUT='mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-base focus:border-[#005AAB] focus:outline-none focus:ring-4 focus:ring-blue-100';
const LABELS={movement_date:'Movement date',kind:'What happened? (required)',amount:'Amount in KES',reference:'Reference (optional)',note:'What was this cash for? (optional)',reason:'Why are you changing this cash movement?'};

function MovementDetails({details}) {
  if(!details)return null;
  return <dl className="grid gap-3 sm:grid-cols-2"><div><dt className="text-sm text-slate-600">Movement date</dt><dd>{details.movement_date}</dd></div><div><dt className="text-sm text-slate-600">Kind</dt><dd className="font-bold">{MOVEMENT_KINDS[details.kind]}</dd></div><div><dt className="text-sm text-slate-600">Amount</dt><dd className="font-bold">{formatKes(details.amount)}</dd></div><div><dt className="text-sm text-slate-600">State</dt><dd>{details.is_voided ? 'Reversed — excluded from till totals' : 'Recorded'}</dd></div>{details.reference ? <div><dt className="text-sm text-slate-600">Reference</dt><dd className="break-words">{details.reference}</dd></div> : null}{details.note ? <div><dt className="text-sm text-slate-600">Note</dt><dd className="whitespace-pre-wrap break-words">{details.note}</dd></div> : null}</dl>;
}

function MovementEditor({movementId,initialDate}) {
  const {authenticatedRequest}=useAuth();
  const save=usePendingSave(movementId ? `/till-movements/${movementId}/corrections` : '/till-movements');
  const [record,setRecord]=useState(null), [loading,setLoading]=useState(Boolean(movementId)), [reload,setReload]=useState(0), [stale,setStale]=useState(false);
  const [form,setForm]=useState({movement_date:initialDate,kind:'',amount:'',reference:'',note:'',reason:'',is_voided:false});
  const [errors,setErrors]=useState({}), [error,setError]=useState(''), [message,setMessage]=useState('');
  const feedback=useRef(null), values=pendingMovementValues(save.pending) || form;
  const locked=loading || stale || save.isSaving || Boolean(save.pending) || !save.ready || (!movementId && Boolean(record));
  const closeDate=record?.movement_date || values.movement_date || initialDate;

  useEffect(()=>{
    if(!movementId)return;
    const controller=new AbortController();
    void authenticatedRequest(`/till-movements/${movementId}`,{signal:controller.signal,cache:'no-store'})
      .then(saved=>{if(!controller.signal.aborted){setRecord(saved);setForm({...saved,reason:''});setStale(false);}})
      .catch(loadError=>{if(!controller.signal.aborted)setError(getUserMessage(loadError,'The cash movement could not be loaded.'));})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[authenticatedRequest,movementId,reload]);
  function edit(key,value){setForm(previous=>({...previous,[key]:value}));setErrors(previous=>({...previous,[key]:''}));setMessage('');}
  function reloadSaved(){setLoading(true);setError('');setMessage('');setErrors({});setReload(value=>value+1);}
  async function submit(event,retry=false) {
    event?.preventDefault();setError('');setMessage('');
    const prepared=movementBody(form,movementId ? record : null);
    if(!retry && Object.keys(prepared.errors).length){setErrors(prepared.errors);feedback.current?.focus();return;}
    setErrors({});
    try {
      const saved=retry ? await save.retry() : await save.save(prepared.body);
      setRecord(saved);setForm({...saved,reason:''});
      setMessage(movementId ? 'Correction saved. The original cash movement and every earlier change remain below.' : `Cash movement #${saved.id} saved once. Return to Close the day to refresh its figures.`);
    } catch(saveError){setError(getUserMessage(saveError,'The cash movement could not be confirmed.'));if(saveError.code==='QLMS-STALE-RECORD')setStale(true);feedback.current?.focus();}
  }
  return <section className="mx-auto max-w-3xl space-y-5">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-bold uppercase tracking-widest text-[#005AAB]">Owner money control</p><h1 className="mt-2 text-3xl font-bold">{movementId ? `Cash movement #${movementId}` : 'Cash added or withdrawn'}</h1></div><Link className="secondary-button" href={`/daily-close?date=${closeDate}`}>Close the day</Link></header>
    <p className="text-slate-600">Record money added to the shop&apos;s till or cash taken by the Owner. These movements are not income or business expenses. Record purchases and wages in <Link className="font-bold text-[#005AAB] underline" href="/expenses">Expenses</Link>; do not record the same payment twice.</p>
    <PendingSaveNotice {...save} onRetry={()=>submit(null,true)}/>
    <div ref={feedback} tabIndex={-1} role={error || Object.values(errors).some(Boolean) ? 'alert' : undefined} className={error || Object.values(errors).some(Boolean) ? 'rounded-xl border border-red-300 bg-red-50 p-4 text-red-800' : ''}>{error || (Object.values(errors).some(Boolean) ? 'Check these details before saving.' : '')}{Object.entries(errors).filter(([,text])=>text).length ? <ul className="mt-2 space-y-2">{Object.entries(errors).filter(([,text])=>text).map(([key,text])=><li key={key}><a className="underline" href={`#movement-${key}`}>{text}</a></li>)}</ul> : null}</div>
    {message ? <p role="status" className="rounded-xl border border-green-300 bg-green-50 p-4 text-green-900">{message}</p> : null}
    {loading ? <p role="status">Loading saved cash movement… QLMS may need a moment to wake up.</p> : movementId && !record ? <button className="secondary-button" type="button" onClick={reloadSaved}>Try loading again</button> : <>
      {record ? <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="mb-4 text-xl font-bold">Saved details</h2><MovementDetails details={record}/><p className="mt-4 text-sm text-slate-600">Recorded by {record.confirmed_by_username} · {formatNairobiDateTime(record.created_at)} · {record.revision} corrections</p>{!movementId ? <div className="mt-4 flex flex-wrap gap-3"><Link className="secondary-button" href={`/till-movements?id=${record.id}`}>Open correction history</Link><a className="secondary-button" href={`/till-movements?date=${record.movement_date}`}>Record another movement</a></div> : null}</section> : null}
      {(!record || movementId) ? <form onSubmit={submit} noValidate className="rounded-2xl border border-slate-200 bg-white p-5"><fieldset id="movement-entry-step" disabled={locked} className="space-y-5"><legend className="mb-4 text-xl font-bold">{movementId ? 'Correct this movement' : 'Cash movement details'}</legend><div className="grid gap-5 sm:grid-cols-2">{[...MOVEMENT_FIELDS,...(movementId ? ['reason'] : [])].map(key=><div key={key} className={['note','reason'].includes(key) ? 'sm:col-span-2' : ''}><label className="block font-bold" htmlFor={`movement-${key}`}>{LABELS[key]}</label>{key==='kind' ? <select className={INPUT} id="movement-kind" value={values.kind} onChange={event=>edit('kind',event.target.value)} aria-required="true" aria-invalid={Boolean(errors.kind)} aria-describedby={errors.kind ? 'movement-error-kind' : undefined}><option value="">Choose what happened</option>{Object.entries(MOVEMENT_KINDS).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select> : key==='note' ? <textarea className={`${INPUT} min-h-24 py-3`} id="movement-note" value={values.note} maxLength={1000} onChange={event=>edit('note',event.target.value)} aria-invalid={Boolean(errors.note)} aria-describedby={errors.note ? 'movement-error-note' : undefined}/> : <input className={INPUT} id={`movement-${key}`} type={key==='movement_date' ? 'date' : 'text'} max={key==='movement_date' ? nairobiToday() : undefined} inputMode={key==='amount' ? 'decimal' : undefined} value={values[key]} maxLength={key==='reference' ? 100 : key==='reason' ? 200 : undefined} autoComplete="off" onChange={event=>edit(key,event.target.value)} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `movement-error-${key}` : undefined}/>} {errors[key] ? <p className="mt-2 text-sm font-semibold text-red-800" id={`movement-error-${key}`}>{errors[key]}</p> : null}</div>)}</div>
        {movementId ? <label className="flex min-h-12 items-start gap-3 rounded-xl bg-amber-50 p-4"><input className="mt-1 size-5" type="checkbox" checked={Boolean(values.is_voided)} onChange={event=>edit('is_voided',event.target.checked)}/><span><strong>Reverse this cash movement</strong><br/>Keep its history but exclude it from till totals. Clear this choice to restore it, explaining why.</span></label> : null}
        <button className="primary-button min-h-12" type="submit" aria-busy={save.isSaving}>{save.isSaving ? 'Saving…' : movementId ? 'Save correction' : 'Save cash movement'}</button>
      </fieldset></form> : null}
      {movementId ? <><button className="secondary-button" type="button" disabled={save.isSaving || Boolean(save.pending) || !save.ready} onClick={reloadSaved}>Reload saved details</button><section id="movement-history-step" className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">Original movement and corrections</h2><div className="rounded-xl bg-slate-50 p-4"><h3 className="mb-3 font-bold">Original movement</h3><MovementDetails details={record.original_details}/></div>{record.corrections.length ? <ol className="space-y-4">{record.corrections.map(change=><li className="rounded-xl border border-slate-200 p-4" key={change.id}><h3 className="font-bold">Correction {change.revision}</h3><p className="mt-2 break-words">{change.reason}</p><p className="my-3 text-sm text-slate-600">{change.confirmed_by_username} · {formatNairobiDateTime(change.created_at)}</p><details><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">Before this change</summary><MovementDetails details={change.before_details}/></details><h4 className="my-3 font-bold">After this change</h4><MovementDetails details={change.after_details}/></li>)}</ol> : <p>No corrections. The original movement is still current.</p>}</section></> : null}
    </>}
    <Link className="secondary-button" href="/reports?report=till">Cash movement history and downloads</Link>
  </section>;
}

function MovementSelection(){const parameters=useSearchParams(),id=parameters.has('id') ? readRecordId(parameters) : null,day=parameters.get('date') || nairobiToday();return (parameters.has('id') && id===null) || !isBusinessDate(day) ? <p role="alert">This cash movement link is not valid. Open Cash added and Owner withdrawals in Reports and choose it again.</p> : <MovementEditor key={id || day} movementId={id} initialDate={day}/>;}
export default function TillMovementsPage(){return <OwnerGuard><Suspense fallback={<p role="status">Opening cash movements…</p>}><MovementSelection/></Suspense></OwnerGuard>;}
