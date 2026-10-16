import { nairobiToday } from './report-tools.js';

export const CLOSE_FIELDS = ['opening_cash', 'counted_cash', 'statement_received', 'statement_returned'];
export const MOVEMENT_FIELDS = ['movement_date', 'kind', 'amount', 'reference', 'note'];
export const MOVEMENT_KINDS = {addition:'Cash added to the till',withdrawal:'Owner withdrawal'};

export function isBusinessDate(value, today = nairobiToday()) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value) || value > today) return false;
  const day = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(day.valueOf()) && day.toISOString().slice(0,10) === value;
}

function cents(value, input = false) {
  if (typeof value !== 'string' && typeof value !== 'number') return null;
  const text = String(value).trim();
  if (!/^\d+(\.\d{1,2})?$/.test(text)) return null;
  const [whole, fraction = ''] = text.split('.');
  const result = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  return Number.isSafeInteger(result) && (!input || result <= 999999999900) ? result : null;
}

export function closingPreview(activity, values) {
  if (!activity) return null;
  const inputs = CLOSE_FIELDS.map(key => cents(values[key], true));
  const sourceKeys = ['cash_received','cash_refunds','shop_cash_expenses','till_additions','owner_withdrawals','mpesa_received','mpesa_refunds'];
  const source = sourceKeys.map(key => cents(activity[key]));
  if ([...inputs,...source].some(value => value === null)) return null;
  const [opening, counted, received, returned] = inputs;
  const [cashReceived, cashRefunds, costs, additions, withdrawals, mpesaReceived, mpesaRefunds] = source;
  const expected = opening + cashReceived - cashRefunds - costs + additions - withdrawals;
  const result = {expected_cash:expected,cash_difference:counted-expected,
    mpesa_received_difference:received-mpesaReceived,mpesa_returned_difference:returned-mpesaRefunds};
  return Object.values(result).every(Number.isSafeInteger) ? result : null;
}

export function formatCents(value) {
  if (!Number.isSafeInteger(value)) return 'Check figures';
  const absolute = Math.abs(value), remainder = absolute % 100;
  return `${value < 0 ? '-' : ''}KES ${Math.trunc(absolute / 100).toLocaleString('en-KE')}${remainder ? `.${String(remainder).padStart(2,'0')}` : ''}`;
}

export function differenceText(value, kind = 'cash') {
  if (!Number.isSafeInteger(value)) return 'Check figures';
  if (value === 0) return 'Matches';
  const amount = formatCents(Math.abs(value));
  return kind === 'statement' ? `Statement shows ${amount} ${value > 0 ? 'more' : 'less'}` : `${amount} ${value > 0 ? 'extra' : 'short'}`;
}

export function differenceFromKes(value, kind = 'cash') {
  const text=String(value), negative=text.startsWith('-');
  const amount=cents(negative ? text.slice(1) : text);
  return amount === null ? 'Check figures' : differenceText(negative ? -amount : amount,kind);
}

function reasonError(value, required, requiredMessage = 'Explain the difference or why you are confirming again.') {
  if (typeof value !== 'string' || value.length > 200 || /[\x00-\x1f\x7f]/.test(value)) return 'Use a plain explanation of at most 200 characters.';
  return required && !value.trim() ? requiredMessage : '';
}

export function closeBody(values, preview) {
  const errors = {}, body = {};
  for (const key of CLOSE_FIELDS) {
    if (cents(values[key],true) === null) errors[key] = 'Enter KES 0 or more, using at most two decimal places.';
    body[key] = typeof values[key] === 'string' ? values[key].trim() : values[key];
  }
  if (!preview || !/^\d{4}-\d{2}-\d{2}$/.test(preview.date) || !/^[0-9a-f]{64}$/.test(preview.activity?.source_fingerprint || '')) errors.preview = 'Load and check this day before confirming.';
  else if (preview.activity.unconfirmed_cash_expenses?.length) errors.preview = 'Confirm who paid the listed cash expenses, then reload this day.';
  const figures = closingPreview(preview?.activity,values);
  if (!figures && !Object.keys(errors).length) errors.preview = 'Reload the day; its money figures could not be checked.';
  const needsReason = Boolean(preview?.latest) || Boolean(figures && ['cash_difference','mpesa_received_difference','mpesa_returned_difference'].some(key => figures[key] !== 0));
  const reason = reasonError(values.reason,needsReason);
  if (reason) errors.reason = reason;
  return {errors,body:{...body,business_date:preview?.date,expected_revision:preview?.latest?.revision || 0,
    expected_fingerprint:preview?.activity?.source_fingerprint,reason:typeof values.reason === 'string' ? values.reason.trim() : ''}};
}

export function pendingCloseValues(pending) {
  try {
    const body=JSON.parse(pending?.body);
    return body && CLOSE_FIELDS.every(key=>typeof body[key] === 'string') && typeof body.business_date === 'string'
      ? {...Object.fromEntries(CLOSE_FIELDS.map(key=>[key,body[key]])),reason:body.reason || '',business_date:body.business_date} : null;
  } catch { return null; }
}

export function movementBody(values, record = null, today = nairobiToday()) {
  const body=Object.fromEntries(MOVEMENT_FIELDS.map(key=>[key,typeof values[key] === 'string' ? values[key].trim() : ''])), errors={};
  if (!isBusinessDate(body.movement_date,today)) errors.movement_date='Choose today or an earlier date.';
  if (!Object.hasOwn(MOVEMENT_KINDS,body.kind)) errors.kind='Choose Cash added to the till or Owner withdrawal.';
  const amount=cents(body.amount,true);
  if (amount === null || amount <= 0) errors.amount='Enter KES 0.01 or more, using at most two decimal places.';
  if (body.reference.length > 100 || /[\x00-\x1f\x7f]/.test(body.reference)) errors.reference='Use a reference of at most 100 characters without line breaks.';
  if (body.note.length > 1000 || /[\x00-\x09\x0b-\x1f\x7f]/.test(body.note)) errors.note='Use a note of at most 1,000 characters without control characters.';
  if (record) {
    body.expected_revision=record.revision; body.is_voided=Boolean(values.is_voided);
    body.reason=typeof values.reason === 'string' ? values.reason.trim() : '';
    const reason=reasonError(body.reason,true,'Explain why this cash movement is changing.'); if(reason) errors.reason=reason;
  }
  return {body,errors};
}

export function pendingMovementValues(pending) {
  try {
    const body=JSON.parse(pending?.body);
    return body && MOVEMENT_FIELDS.every(key=>typeof body[key] === 'string') ? body : null;
  } catch { return null; }
}
