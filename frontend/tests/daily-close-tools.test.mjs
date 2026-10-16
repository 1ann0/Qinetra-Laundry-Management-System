import test from 'node:test';
import assert from 'node:assert/strict';
import { closingPreview, closeBody, differenceText, pendingCloseValues, movementBody, pendingMovementValues, differenceFromKes } from '../src/lib/daily-close-tools.js';

const activity = {cash_received:'1000.00', cash_refunds:'100.00', shop_cash_expenses:'150.00',
  owner_cash_expenses:'300.00', till_additions:'50.00', owner_withdrawals:'100.00',
  mpesa_received:'700.00', mpesa_refunds:'50.00', source_fingerprint:'a'.repeat(64), unconfirmed_cash_expenses:[]};
const values = {opening_cash:'200', counted_cash:'850', statement_received:'700', statement_returned:'50', reason:''};
const preview = {date:'2026-10-13',activity,latest:null};

test('phone preview gives KES 900 expected, KES 50 short and separate matching M-Pesa totals',()=>{
  const result=closingPreview(activity,values);
  assert.equal(result.expected_cash,90000);
  assert.equal(result.cash_difference,-5000);
  assert.equal(result.mpesa_received_difference,0);
  assert.equal(result.mpesa_returned_difference,0);
  assert.equal(differenceText(result.cash_difference),'KES 50 short');
  assert.equal(differenceText(125),'KES 1.25 extra');
  assert.equal(differenceText(0),'Matches');
});

test('exact cents and statement direction do not use binary decimal subtraction',()=>{
  const result=closingPreview({...activity,cash_received:'0',cash_refunds:'0',shop_cash_expenses:'0',till_additions:'0',owner_withdrawals:'0'},
    {...values,opening_cash:'0.30',counted_cash:'0.10'});
  assert.equal(result.cash_difference,-20);
  assert.equal(differenceText(-20),'KES 0.20 short');
  assert.equal(differenceText(-5000,'statement'),'Statement shows KES 50 less');
  assert.equal(differenceText(5000,'statement'),'Statement shows KES 50 more');
  assert.equal(differenceFromKes('-0.20'),'KES 0.20 short');
  assert.equal(differenceFromKes('50','statement'),'Statement shows KES 50 more');
});

test('a variance or later sign-off requires an explanation and counts remain manual',()=>{
  assert.ok(closeBody(values,preview).errors.reason);
  const saved=closeBody({...values,reason:'Fictional cash short'},preview);
  assert.deepEqual(saved.errors,{});
  assert.equal(saved.body.expected_fingerprint,activity.source_fingerprint);
  assert.equal(saved.body.expected_revision,0);
  assert.equal(saved.body.counted_cash,'850');
  assert.equal(Object.hasOwn(saved.body,'expected_cash'),false);
  assert.ok(closeBody({...values,counted_cash:'900'}, {...preview,latest:{revision:1}}).errors.reason);
});

test('blank, negative, boolean, excessive decimals and oversized amounts stay invalid',()=>{
  for(const bad of ['', '-1', true, '1.001', 'NaN', '10000000000'])
    assert.ok(closeBody({...values,opening_cash:bad},preview).errors.opening_cash,String(bad));
  assert.equal(closingPreview(activity,{...values,opening_cash:''}),null);
});

test('missing snapshot and unconfirmed cash funding prevent a fresh sign-off',()=>{
  assert.ok(closeBody(values,null).errors.preview);
  assert.ok(closeBody(values,{...preview,activity:{...activity,unconfirmed_cash_expenses:[{id:1,amount:'25'}]}}).errors.preview);
  assert.ok(closeBody(values,{...preview,activity:{...activity,shop_cash_expenses:undefined}}).errors.preview);
});

test('pending counts derive from the original body without replacing the saved fingerprint',()=>{
  const body=JSON.stringify({...values,business_date:'2026-10-13',expected_revision:0,expected_fingerprint:'b'.repeat(64)});
  const pending={key:'fictional-reference',body};
  assert.equal(pendingCloseValues(pending).counted_cash,'850');
  assert.equal(pendingCloseValues(pending).business_date,'2026-10-13');
  assert.equal(pending.body,body);
  assert.equal(pendingCloseValues({body:'bad'}),null);
});

test('cash movement needs a positive amount and corrections require an attributed reason',()=>{
  const fields={movement_date:'2026-10-13',kind:'withdrawal',amount:'50',reference:'Fictional drawing',note:''};
  assert.deepEqual(movementBody(fields,null,'2026-10-13').errors,{});
  assert.ok(movementBody({...fields,amount:'0'},null,'2026-10-13').errors.amount);
  assert.ok(movementBody({...fields,kind:''},null,'2026-10-13').errors.kind);
  assert.ok(movementBody({...fields,movement_date:'2026-10-14'},null,'2026-10-13').errors.movement_date);
  const record={revision:1};
  assert.ok(movementBody(fields,record,'2026-10-13').errors.reason);
  const corrected=movementBody({...fields,reason:'Fictional corrected withdrawal',is_voided:true},record,'2026-10-13');
  assert.deepEqual(corrected.errors,{});
  assert.equal(corrected.body.expected_revision,1);
  assert.equal(corrected.body.is_voided,true);
  const pending={body:JSON.stringify(corrected.body)};
  assert.equal(pendingMovementValues(pending).reason,'Fictional corrected withdrawal');
  assert.equal(pendingMovementValues({body:'bad'}),null);
});
