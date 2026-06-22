"use client";

import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AppShell } from "@/components/layout/AppShell";
import { TopologyGraph } from "@/components/topology/TopologyGraph";
import { ClusterSelector } from "@/components/ClusterSelector";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { useClusters, resolveDefaultCluster } from "@/hooks/useClusters";
import { useTopology } from "@/hooks/useTopology";
import { filterTopology, getUniqueNamespaces } from "@/lib/topologyLayout";

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return "Unable to load cluster topology.";
}

export default function TopologyPage() {
  const [clusterId, setClusterId] = useState("");
  const [namespaceFilter, setNamespaceFilter] = useState("all");

  const clustersQuery = useClusters();
  const topologyQuery = useTopology(clusterId, undefined, Boolean(clusterId));

  useEffect(() => {
    if (clustersQuery.data?.clusters?.length && !clusterId) {
      setClusterId(resolveDefaultCluster(clustersQuery.data.clusters));
    }
  }, [clustersQuery.data, clusterId]);

  const filteredData = useMemo(() => {
    if (!topologyQuery.data) {
      return null;
    }
    return filterTopology(topologyQuery.data, namespaceFilter);
  }, [topologyQuery.data, namespaceFilter]);

  const namespaces = useMemo(
    () => (topologyQuery.data ? getUniqueNamespaces(topologyQuery.data) : []),
    [topologyQuery.data],
  );

  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="panel-subtitle mb-1">Resource Map</p>
              <h2 className="panel-title">Cluster Topology</h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
                Interactive map of namespaces, workloads, services, ingress routes, and their
                relationships across the selected cluster.
              </p>
            </div>

            <div className="flex w-full flex-col gap-4 lg:max-w-3xl">
              <ClusterSelector
                clusters={clustersQuery.data?.clusters ?? []}
                clusterId={clusterId}
                onClusterChange={setClusterId}
                loading={clustersQuery.isLoading}
                error={clustersQuery.data?.error ?? null}
                label="Cluster"
                compact
              />

              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label htmlFor="topology-namespace" className="section-label">
                    Namespace
                  </label>
                  <select
                    id="topology-namespace"
                    value={namespaceFilter}
                    onChange={(event) => setNamespaceFilter(event.target.value)}
                    className="input-field min-w-[180px]"
                    disabled={!topologyQuery.data}
                  >
                    <option value="all">All namespaces</option>
                    {namespaces.map((namespace) => (
                      <option key={namespace} value={namespace}>
                        {namespace}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => topologyQuery.refetch()}
                  disabled={topologyQuery.isFetching || !clusterId}
                  className="btn-primary min-w-[140px]"
                >
                  {topologyQuery.isFetching ? "Refreshing..." : "Refresh map"}
                </button>
              </div>
            </div>
          </div>

          {topologyQuery.isLoading && (
            <div className="alert-loading flex items-center gap-3">
              <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-brand-500/30 border-t-brand-400" />
              Discovering cluster topology...
            </div>
          )}

          {topologyQuery.isError && (
            <div className="alert-error">{getErrorMessage(topologyQuery.error)}</div>
          )}

          {filteredData && !topologyQuery.isLoading && (
            <div className="panel-accent p-5">
              <TopologyGraph data={filteredData} />
            </div>
          )}
        </div>
      </AppShell>
    </RequireAuth>
  );
}
