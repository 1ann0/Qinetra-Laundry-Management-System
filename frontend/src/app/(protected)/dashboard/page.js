import OwnerGuard from "@/components/auth/owner-guard";

export default function DashboardPage() {
  return (
    <OwnerGuard>
      <section className="dashboard-card">
        <p className="eyebrow">Owner access confirmed</p>
        <h1>Dashboard</h1>
        <p>
          This route is reserved for the owner. Order totals, overdue counts, and
          CSV export will be implemented in Phase 5.
        </p>
      </section>
    </OwnerGuard>
  );
}
