import { RequireAuth } from "@/components/auth/RequireAuth";
import { SchedulesPage } from "@/modules/kubernetes/SchedulesPage";

export default function KubernetesSchedulesRoute() {
  return (
    <RequireAuth>
      <SchedulesPage />
    </RequireAuth>
  );
}
