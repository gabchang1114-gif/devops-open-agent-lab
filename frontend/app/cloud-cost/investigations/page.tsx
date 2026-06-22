"use client";

import { AppShell } from "@/components/layout/AppShell";
import { InvestigationHistory } from "@/components/InvestigationHistory";
import { RequireAuth } from "@/components/auth/RequireAuth";

export default function CloudCostInvestigationsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <InvestigationHistory
          agentFilter="cloud_cost"
          scopeColumnLabel="Account / Region"
          emptyStateHref="/cloud-cost"
          emptyStateLabel="Run your first cost analysis"
          backBasePath="/cloud-cost/investigations"
        />
      </AppShell>
    </RequireAuth>
  );
}
