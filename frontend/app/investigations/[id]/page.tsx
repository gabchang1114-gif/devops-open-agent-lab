"use client";

import { use, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { InvestigationDetailView } from "@/components/InvestigationDetailView";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { useInvestigationHistory } from "@/hooks/useInvestigationStatus";

export default function InvestigationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const backHref = searchParams.get("from") || "/investigations";
  const agentFilter = backHref.startsWith("/aws")
    ? "aws"
    : backHref.startsWith("/cloud-cost")
      ? "cloud_cost"
      : "kubernetes";
  const { data } = useInvestigationHistory(agentFilter);
  const summary = useMemo(
    () => data?.investigations.find((item) => item.id === id) ?? null,
    [data?.investigations, id],
  );

  return (
    <RequireAuth>
      <AppShell>
        <InvestigationDetailView
          investigationId={id}
          summary={summary}
          backHref={backHref}
        />
      </AppShell>
    </RequireAuth>
  );
}
