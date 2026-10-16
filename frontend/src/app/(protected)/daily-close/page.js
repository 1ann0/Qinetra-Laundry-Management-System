"use client";

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import OwnerGuard from '@/components/auth/owner-guard';
import PendingSaveNotice from '@/components/orders/pending-save-notice';
import usePendingSave from '@/components/orders/use-pending-save';
import { useAuth } from '@/context/auth-context';
import { formatNairobiDateTime } from '@/lib/format-nairobi';
import { formatKes, nairobiToday } from '@/lib/report-tools';
import { getUserMessage } from '@/lib/user-messages';
import { CLOSE_FIELDS, closeBody, closingPreview, differenceText, differenceFromKes, formatCents, isBusinessDate, pendingCloseValues, MOVEMENT_KINDS } from '@/lib/daily-close-tools';

const INPUT='mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-base focus:border-[#005AAB] focus:outline-none focus:ring-4 focus:ring-blue-100';
const LABELS={opening_cash:'Starting cash, before today’s movements',counted_cash:'Cash counted now',statement_received:'Shop M-Pesa collected — statement total',statement_returned:'Shop M-Pesa returned — statement total',reason:'Explanation (required for differences or a new confirmation)'};
const EMPTY={opening_cash:'',counted_cash:'',statement_received:'',statement_returned:'',reason:''};
const ACTIVITY_LABELS=[['cash_received','Cash received'],['cash_refunds','Cash returned to customers'],['shop_cash_expenses','Cash expenses paid from the till'],['till_additions','Cash added to the till'],['owner_withdrawals','Owner withdrawals'],['owner_cash_expenses','Personally paid cash costs — not taken from till'],['mpesa_received','M-Pesa collected'],['mpesa_refunds','M-Pesa returned to customers']];

function SignedClose({record}) {
  const {counts,figures}=record.snapshot;
  return <div className="space-y-3 rounded-xl border border-slate-200 p-4">
    <h3 className="font-bold">Owner confirmation {record.revision} · {record.business_date}</h3>
    <p className="text-sm text-slate-600">{record.confirmed_by_username} · {formatNairobiDateTime(record.created_at)}</p>
    <dl className="grid gap-3 sm:grid-cols-2">
      <div><dt>Expected cash</dt><dd className="font-bold">{formatKes(figures.expected_cash)}</dd></div>
      <div><dt>Counted cash</dt><dd className="font-bold">{formatKes(counts.counted_cash)}</dd></div>
      <div><dt>Cash difference</dt><dd>{differenceFromKes(figures.cash_difference)}</dd></div>
      <div><dt>Opening cash entered</dt><dd>{formatKes(counts.opening_cash)}</dd></div>
      <div><dt>Statement M-Pesa collected</dt><dd>{formatKes(counts.statement_received)}</dd></div>
      <div><dt>Statement M-Pesa returned</dt><dd>{formatKes(counts.statement_returned)}</dd></div>
      <div><dt>M-Pesa collected difference</dt><dd>{differenceFromKes(figures.mpesa_received_difference,'statement')}</dd></div>
      <div><dt>M-Pesa returned difference</dt><dd>{differenceFromKes(figures.mpesa_returned_difference,'statement')}</dd></div>
    </dl>
    {record.reason ? <p className="break-words"><strong>Explanation:</strong> {record.reason}</p> : null}
    <details><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">Activity included in this confirmation</summary><dl className="mt-3 grid gap-3 sm:grid-cols-2">{ACTIVITY_LABELS.map(([key,label])=><div key={key}><dt className="text-sm text-slate-600">{label}</dt><dd>{formatKes(record.snapshot.activity[key])}</dd></div>)}</dl></details>
    <p className="text-sm text-slate-600">These are the figures confirmed at that time. Later activity does not rewrite them.</p>
  </div>;
}

function CloseEditor({initialDate}) {
  const {authenticatedRequest}=useAuth();
  const save=usePendingSave('/daily-close');
  const [day,setDay]=useState(initialDate), [requestedDay,setRequestedDay]=useState(initialDate);
  const [preview,setPreview]=useState(null), [loading,setLoading]=useState(true), [reload,setReload]=useState(0);
  const [form,setForm]=useState({...EMPTY}), [errors,setErrors]=useState({}), [error,setError]=useState(''), [message,setMessage]=useState(''), [stale,setStale]=useState(false);
  const feedback=useRef(null);
  const pendingValues=pendingCloseValues(save.pending), values=pendingValues || form;
  const displayedDay=pendingValues?.business_date || day;
  const requestTarget=pendingValues?.business_date || requestedDay;
  const current=preview?.date===displayedDay ? preview : null;
  const figures=closingPreview(current?.activity,values);
  const locked=loading || save.isSaving || Boolean(save.pending) || !save.ready;

  useEffect(()=>{
    const controller=new AbortController();
    void authenticatedRequest(`/daily-close?date=${encodeURIComponent(requestTarget)}`,{signal:controller.signal,cache:'no-store'})
      .then(result=>{if(!controller.signal.aborted){setPreview(result);setStale(false);}})
      .catch(loadError=>{if(!controller.signal.aborted)setError(getUserMessage(loadError,'The day could not be loaded.'));})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[authenticatedRequest,requestTarget,reload]);

  function loadDay() {
    if(!isBusinessDate(day)){setErrors({date:'Choose today or an earlier date.'});feedback.current?.focus();return;}
    if(day!==requestedDay)setForm({...EMPTY});
    setErrors({});setError('');setMessage('');setLoading(true);setPreview(null);setRequestedDay(day);setReload(value=>value+1);
  }
  function edit(key,value){setForm(previous=>({...previous,[key]:value}));setErrors(previous=>({...previous,[key]:''}));setMessage('');}
  async function submit(event,retry=false) {
    event?.preventDefault();setError('');setMessage('');
    const prepared=closeBody(form,current);
    if(!retry && Object.keys(prepared.errors).length){setErrors(prepared.errors);feedback.current?.focus();return;}
    setErrors({});
    if(retry && pendingValues){setForm(Object.fromEntries([...CLOSE_FIELDS,'reason'].map(key=>[key,pendingValues[key]])));setDay(pendingValues.business_date);setRequestedDay(pendingValues.business_date);}
    try {
      const signed=retry ? await save.retry() : await save.save(prepared.body);
      setForm(previous=>({...previous,reason:''}));
      setMessage(`Owner confirmation ${signed.revision} saved once. Earlier confirmations remain in history.`);
      setDay(signed.business_date);setRequestedDay(signed.business_date);setLoading(true);setReload(value=>value+1);
    } catch(saveError){setError(getUserMessage(saveError,'The closing could not be confirmed.'));if(saveError.code==='QLMS-STALE-RECORD')setStale(true);feedback.current?.focus();}
  }

  return <section className="mx-auto max-w-4xl space-y-5">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-sm font-bold uppercase tracking-widest text-[#005AAB]">Owner money control</p><h1 className="mt-2 text-3xl font-bold">Close the day</h1></div><Link className="secondary-button" href="/finance">Finance</Link></header>
    <p className="text-slate-600">Choose a day, count the cash and compare M-Pesa collections and returns with the statement. Explain any difference, then confirm.</p>
    <PendingSaveNotice {...save} onRetry={()=>submit(null,true)}/>
    {save.pending ? <p role="status" className="rounded-xl bg-amber-50 p-4">Resolve the previous confirmation for {displayedDay} first. Retry keeps its original counts, date and save reference.</p> : null}
    <div ref={feedback} tabIndex={-1} role={error || Object.values(errors).some(Boolean) ? 'alert' : undefined} className={error || Object.values(errors).some(Boolean) ? 'rounded-xl border border-red-300 bg-red-50 p-4 text-red-800' : ''}>
      {error || (Object.values(errors).some(Boolean) ? 'Check these details before confirming.' : '')}
      {Object.entries(errors).filter(([,text])=>text).length ? <ul className="mt-2 space-y-2">{Object.entries(errors).filter(([,text])=>text).map(([key,text])=><li key={key}><a className="underline" href={key==='preview' ? '#close-date-step' : `#close-${key}`}>{text}</a></li>)}</ul> : null}
    </div>
    {message ? <p role="status" className="rounded-xl border border-green-300 bg-green-50 p-4 text-green-900">{message}</p> : null}
    <div id="close-date-step" className="rounded-2xl border border-slate-200 bg-white p-5"><label className="block font-bold" htmlFor="close-date">Business date · Nairobi</label><input className={INPUT} id="close-date" type="date" max={nairobiToday()} value={displayedDay} disabled={locked} onChange={event=>setDay(event.target.value)} aria-invalid={Boolean(errors.date)}/><button className="secondary-button mt-4" type="button" disabled={loading || save.isSaving || Boolean(save.pending) || !save.ready} onClick={loadDay}>{loading ? 'Loading figures…' : 'Load / reload this day'}</button></div>
    {loading ? <p role="status">Loading the day&apos;s records… QLMS may need a moment to wake up. Your entered counts stay here.</p> : !current ? <p role="status">Load this day before entering its closing figures.</p> : <>
      <section id="close-activity-step" className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">1. Check recorded activity · {current.date}</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">{ACTIVITY_LABELS.map(([key,label])=><div key={key}><dt className="text-sm text-slate-600">{label}</dt><dd className="font-bold">{formatKes(current.activity[key])}</dd></div>)}</dl>
        <div className="mt-4 flex flex-wrap gap-3"><Link className="secondary-button" href={`/till-movements?date=${current.date}`}>Record cash added or withdrawn</Link><Link className="secondary-button" href={`/reports?report=money&start_date=${current.date}&end_date=${current.date}`}>Check payments and returns</Link><Link className="secondary-button" href={`/reports?report=expenses&start_date=${current.date}&end_date=${current.date}`}>Check expenses</Link></div>
        {current.activity.movements.length ? <details className="mt-4"><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">Cash movement records</summary><ul className="space-y-3">{current.activity.movements.map(item=><li key={item.id}><Link className="flex min-h-12 items-center rounded-lg border p-3 text-[#005AAB]" href={`/till-movements?id=${item.id}`}>#{item.id} · {MOVEMENT_KINDS[item.kind]} · {formatKes(item.amount)}{item.is_voided ? ' · Reversed' : ''}</Link></li>)}</ul></details> : null}
        {current.activity.unconfirmed_cash_expenses.length ? <div role="alert" className="mt-4 rounded-xl bg-amber-50 p-4 text-amber-950"><p className="font-bold">Confirm who paid these cash expenses first.</p><p>A personally paid cost must not reduce the shop&apos;s cash. Correct Paid from, then return and reload this day.</p><ul className="mt-2 space-y-2">{current.activity.unconfirmed_cash_expenses.map(item=><li key={item.id}><Link className="inline-flex min-h-12 items-center font-bold underline" href={`/expenses?id=${item.id}`}>Expense #{item.id} · {formatKes(item.amount)}</Link></li>)}</ul></div> : null}
      </section>
      {current.latest ? <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-xl font-bold">{current.needs_review ? 'Needs review — activity changed after confirmation' : 'Owner confirmation saved'}</h2><p>Signed cash result: <strong>{differenceFromKes(current.latest.snapshot.figures.cash_difference)}</strong></p><details><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">View the latest signed figures</summary><SignedClose record={current.latest}/></details></section> : <p>No Owner confirmation has been saved for this day.</p>}
      {stale ? <p role="alert" className="rounded-xl bg-amber-50 p-4">Reload the figures and check them before confirming again. Your entered counts remain in the form.</p> : null}
      <form onSubmit={submit} noValidate className="rounded-2xl border border-slate-200 bg-white p-5"><fieldset disabled={locked || stale || Boolean(current.activity.unconfirmed_cash_expenses.length)} className="space-y-5"><legend id="close-counts-step" className="mb-4 text-xl font-bold">2. Count the money</legend><p className="text-sm text-slate-600">All four amounts are required; enter 0 when there was none. Starting cash is what was there before today&apos;s additions and withdrawals. Count the remaining cash after recording them. Use the statement&apos;s shop collections and returns, not its account balance or expense payments.</p>
        <div className="grid gap-5 sm:grid-cols-2">{CLOSE_FIELDS.map(key=><div key={key}><label className="block font-bold" htmlFor={`close-${key}`}>{LABELS[key]}</label><input className={INPUT} id={`close-${key}`} inputMode="decimal" aria-required="true" autoComplete="off" maxLength={14} value={values[key]} onChange={event=>edit(key,event.target.value)} aria-invalid={Boolean(errors[key])} aria-describedby={errors[key] ? `close-error-${key}` : undefined}/>{errors[key] ? <p className="mt-2 text-sm font-semibold text-red-800" id={`close-error-${key}`}>{errors[key]}</p> : null}</div>)}</div>
        {figures ? <div id="close-comparison-step" className="space-y-3 rounded-xl bg-slate-50 p-4" aria-live="polite"><h2 className="font-bold">3. Check the differences</h2><p>Expected cash: <strong>{formatCents(figures.expected_cash)}</strong></p><p className="font-bold">{differenceText(figures.cash_difference)}</p><p>M-Pesa collected: {differenceText(figures.mpesa_received_difference,'statement')}</p><p>M-Pesa returned: {differenceText(figures.mpesa_returned_difference,'statement')}</p><p className="text-sm text-slate-600">A match is your manual reconciliation result. Receipts and till cash are not profit.</p></div> : <p>Enter all four amounts to see the comparison.</p>}
        <div><label className="block font-bold" htmlFor="close-reason">{LABELS.reason}</label><input className={INPUT} id="close-reason" maxLength={200} value={values.reason} onChange={event=>edit('reason',event.target.value)} aria-invalid={Boolean(errors.reason)} aria-describedby={errors.reason ? 'close-error-reason' : undefined}/>{errors.reason ? <p className="mt-2 text-sm font-semibold text-red-800" id="close-error-reason">{errors.reason}</p> : null}</div>
        <button className="primary-button min-h-12" type="submit" aria-busy={save.isSaving}>{save.isSaving ? 'Confirming…' : current.latest ? 'Confirm day again as Owner' : 'Confirm day as Owner'}</button>
      </fieldset></form>
      <section id="close-history-step" className="space-y-4"><Link className="secondary-button" href={`/reports?report=closing&start_date=${current.date}&end_date=${current.date}`}>Closing report and downloads</Link>{current.history.length>1 ? <details><summary className="flex min-h-12 cursor-pointer items-center font-bold text-[#005AAB]">Earlier Owner confirmations ({current.history.length-1})</summary><div className="mt-3 space-y-4">{current.history.slice(1).map(record=><SignedClose key={record.id} record={record}/>)}</div></details> : null}</section>
    </>}
  </section>;
}

function CloseSelection(){const parameters=useSearchParams(), initialDate=parameters.get('date') || nairobiToday();return isBusinessDate(initialDate) ? <CloseEditor key={initialDate} initialDate={initialDate}/> : <p role="alert">This closing date is not valid. <Link className="underline" href="/daily-close">Choose a day again.</Link></p>;}
export default function DailyClosePage(){return <OwnerGuard><Suspense fallback={<p role="status">Opening daily closing…</p>}><CloseSelection/></Suspense></OwnerGuard>;}
