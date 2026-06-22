"use client";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AwsDashboard } from "@/components/aws/AwsDashboard";

export default function AwsAgentPage() {
  return (
    <RequireAuth>
      <AwsDashboard />
    </RequireAuth>
  );
}
