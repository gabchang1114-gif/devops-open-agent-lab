"use client";

import { AppShell } from "@/components/layout/AppShell";
import { InvestigationHistory } from "@/components/InvestigationHistory";
import { RequireAuth } from "@/components/auth/RequireAuth";

export default function AwsInvestigationsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <InvestigationHistory
          agentFilter="aws"
          scopeColumnLabel="Account / Region"
          emptyStateHref="/aws"
          emptyStateLabel="Run your first AWS investigation"
          backBasePath="/aws/investigations"
        />
      </AppShell>
    </RequireAuth>
  );
}
