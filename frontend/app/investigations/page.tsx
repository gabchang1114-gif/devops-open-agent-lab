"use client";

import { AppShell } from "@/components/layout/AppShell";
import { InvestigationHistory } from "@/components/InvestigationHistory";
import { RequireAuth } from "@/components/auth/RequireAuth";

export default function InvestigationsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <InvestigationHistory
          agentFilter="kubernetes"
          scopeColumnLabel="Cluster"
          emptyStateHref="/"
          emptyStateLabel="Run your first cluster investigation"
          backBasePath="/investigations"
        />
      </AppShell>
    </RequireAuth>
  );
}
