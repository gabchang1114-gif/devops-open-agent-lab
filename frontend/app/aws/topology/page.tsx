"use client";

import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { TopologyGraph } from "@/components/topology/TopologyGraph";
import { awsTopologyToGraph } from "@/lib/awsTopologyAdapter";
import { filterAwsTopologyByVpc, getUniqueVpcs } from "@/lib/topologyLayout";
import { useAwsAccounts, useAwsRegions, useAwsTopology } from "@/hooks/useAwsInvestigation";

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return "Unable to load AWS infrastructure topology.";
}

export default function AwsTopologyPage() {
  const [accountId, setAccountId] = useState("");
  const [region, setRegion] = useState("");
  const [vpcFilter, setVpcFilter] = useState("all");

  const accountsQuery = useAwsAccounts();
  const regionsQuery = useAwsRegions(accountId, region || undefined, Boolean(accountId));
  const topologyQuery = useAwsTopology(accountId, region, Boolean(accountId && region));

  useEffect(() => {
    const accounts = accountsQuery.data?.accounts ?? [];
    if (accounts.length > 0 && !accountId) {
      setAccountId(accounts[0].account_id);
    }
  }, [accountsQuery.data, accountId]);

  useEffect(() => {
    const regions = regionsQuery.data?.regions ?? [];
    if (regions.length > 0 && !region) {
      setRegion(regions[0].region);
    }
  }, [regionsQuery.data, region]);

  useEffect(() => {
    setRegion("");
    setVpcFilter("all");
  }, [accountId]);

  useEffect(() => {
    setVpcFilter("all");
  }, [region]);

  const graphData = useMemo(
    () => (topologyQuery.data ? awsTopologyToGraph(topologyQuery.data) : null),
    [topologyQuery.data],
  );

  const vpcs = useMemo(() => (graphData ? getUniqueVpcs(graphData) : []), [graphData]);

  const filteredData = useMemo(() => {
    if (!graphData) {
      return null;
    }
    return filterAwsTopologyByVpc(graphData, vpcFilter);
  }, [graphData, vpcFilter]);

  return (
    <RequireAuth>
      <AppShell>
        <div className="space-y-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="panel-subtitle mb-1">Resource Map</p>
              <h2 className="panel-title">AWS Infrastructure Topology</h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
                Interactive map of VPCs, subnets, load balancers, EC2 instances, Lambda functions,
                S3 buckets, security groups, and their relationships in the selected region.
              </p>
            </div>

            <div className="flex w-full flex-col gap-4 lg:max-w-3xl">
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label htmlFor="aws-topology-account" className="section-label">
                    Account
                  </label>
                  <select
                    id="aws-topology-account"
                    value={accountId}
                    onChange={(event) => setAccountId(event.target.value)}
                    className="input-field w-full"
                    disabled={accountsQuery.isLoading}
                  >
                    {(accountsQuery.data?.accounts ?? []).map((account) => (
                      <option key={account.account_id} value={account.account_id}>
                        {account.account_name
                          ? `${account.account_name} (${account.account_id})`
                          : account.account_id}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="aws-topology-region" className="section-label">
                    Region
                  </label>
                  <select
                    id="aws-topology-region"
                    value={region}
                    onChange={(event) => setRegion(event.target.value)}
                    className="input-field w-full"
                    disabled={!accountId || regionsQuery.isLoading}
                  >
                    {(regionsQuery.data?.regions ?? []).map((regionInfo) => (
                      <option key={regionInfo.region} value={regionInfo.region}>
                        {regionInfo.region}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label htmlFor="aws-topology-vpc" className="section-label">
                    VPC
                  </label>
                  <select
                    id="aws-topology-vpc"
                    value={vpcFilter}
                    onChange={(event) => setVpcFilter(event.target.value)}
                    className="input-field min-w-[220px]"
                    disabled={!graphData}
                  >
                    <option value="all">All VPCs</option>
                    {vpcs.map((vpc) => (
                      <option key={vpc.id} value={vpc.id}>
                        {vpc.name}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => topologyQuery.refetch()}
                  disabled={topologyQuery.isFetching || !accountId || !region}
                  className="btn-primary min-w-[140px]"
                >
                  {topologyQuery.isFetching ? "Refreshing..." : "Refresh map"}
                </button>
              </div>
            </div>
          </div>

          {accountsQuery.isError && (
            <div className="alert-error">{getErrorMessage(accountsQuery.error)}</div>
          )}

          {topologyQuery.isLoading && (
            <div className="alert-loading flex items-center gap-3">
              <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-orange-500/30 border-t-orange-400" />
              Discovering AWS infrastructure topology...
            </div>
          )}

          {topologyQuery.isError && (
            <div className="alert-error">{getErrorMessage(topologyQuery.error)}</div>
          )}

          {filteredData && !topologyQuery.isLoading && (
            <div className="panel-accent p-5">
              <TopologyGraph data={filteredData} variant="aws" />
            </div>
          )}
        </div>
      </AppShell>
    </RequireAuth>
  );
}
