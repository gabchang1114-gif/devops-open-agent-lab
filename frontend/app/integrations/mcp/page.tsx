import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { McpIntegrationPage } from "@/modules/integrations/McpIntegrationPage";

export default function McpIntegrationRoute() {
  return (
    <RequireAuth>
      <AppShell>
        <McpIntegrationPage />
      </AppShell>
    </RequireAuth>
  );
}
