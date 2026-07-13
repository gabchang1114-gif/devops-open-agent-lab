import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { QdrantIntegrationPage } from "@/modules/integrations/QdrantIntegrationPage";

export default function QdrantIntegrationRoute() {
  return (
    <RequireAuth>
      <AppShell>
        <QdrantIntegrationPage />
      </AppShell>
    </RequireAuth>
  );
}
