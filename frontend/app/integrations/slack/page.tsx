import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { SlackIntegrationPage } from "@/modules/integrations/SlackIntegrationPage";

export default function SlackIntegrationRoute() {
  return (
    <RequireAuth>
      <AppShell>
        <SlackIntegrationPage />
      </AppShell>
    </RequireAuth>
  );
}
