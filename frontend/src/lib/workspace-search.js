// Search only the existing read APIs; it never changes customers, prices or tickets.
export function matchesSearch(query, ...values) {
  const normalize = value => String(value ?? "").normalize("NFKD").replace(/\p{M}/gu, "").replaceAll("_", " ").toLowerCase();
  const text = values.map(normalize).join(" ");
  return normalize(query).trim().split(/\s+/).every(word => text.includes(word));
}

export async function searchWorkspace(request, value) {
  const query = value.trim();
  if (!query || query.length > 100) throw new Error("Enter a name, phone, ticket or service, up to 100 characters.");
  const [customers, orders, services] = await Promise.allSettled([
    request(`/customers?search=${encodeURIComponent(query)}`),
    request(`/orders?search=${encodeURIComponent(query)}`),
    request("/catalog/services?include_inactive=true"),
  ]);
  if (services.status === "fulfilled") {
    services.value = services.value.filter(service => matchesSearch(query, service.name, service.code));
  }
  return {query, customers, orders, services};
}
