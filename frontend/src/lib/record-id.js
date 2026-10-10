// Reject ambiguous links before mounting a record editor or its save scope.
export function readRecordId(searchParams) {
  const values = searchParams.getAll("id");
  if (values.length !== 1 || !/^[1-9]\d*$/.test(values[0])) return null;
  const id = Number(values[0]);
  return Number.isSafeInteger(id) ? id : null;
}
