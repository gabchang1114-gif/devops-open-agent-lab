import { Dashboard } from "@/components/Dashboard";
import { RequireAuth } from "@/components/auth/RequireAuth";

export default function HomePage() {
  return (
    <RequireAuth>
      <main>
        <Dashboard />
      </main>
    </RequireAuth>
  );
}
