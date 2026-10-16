import test from 'node:test';
import assert from 'node:assert/strict';
import { REPORT_TYPES, reportQuery, reportSummaryValue } from '../src/lib/report-tools.js';
import { responseError } from '../src/lib/user-messages.js';

test('closing and cash movements use only date filters and counts are not KES',()=>{
  assert.ok(REPORT_TYPES.some(item=>item.value==='closing'));
  assert.ok(REPORT_TYPES.some(item=>item.value==='till'));
  assert.equal(reportQuery('closing',{start_date:'2026-10-13',payment_method:'cash'}),'start_date=2026-10-13');
  assert.equal(reportSummaryValue('closing','days_confirmed',2),'2');
  assert.equal(reportSummaryValue('closing','days_needing_review',1),'1');
  assert.equal(reportSummaryValue('till','cash_added',50),'KES 50');
  assert.equal(reportSummaryValue('attention','ready',3),'3');
});

test('closing rejections explain the correct next action without exposing arbitrary server text',()=>{
  const payload={detail:{code:'QLMS-STALE-RECORD',save_state:'not_saved',message:'Confirm who paid each unconfirmed cash expense before closing'}};
  const unknown=responseError(409,payload,'/daily-close');
  assert.match(unknown.message,/cash expenses/);
  assert.equal(unknown.saveState,'not_saved');
  const stale=responseError(409,{detail:{...payload.detail,message:'UNTRUSTED_DO_NOT_SHOW'}},'/daily-close');
  assert.match(stale.message,/Reload/);
  assert.doesNotMatch(stale.message,/UNTRUSTED_DO_NOT_SHOW/);
  assert.match(responseError(409,payload,'/expenses/1/corrections').message,/correction/);
});
