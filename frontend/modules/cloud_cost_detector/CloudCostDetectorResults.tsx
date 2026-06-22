"use client";

import type { ReactNode } from "react";
import type { CloudCostAnalyzeResponse } from "@/types/cloudCost";

interface CloudCostDetectorResultsProps {
  data: CloudCostAnalyzeResponse;
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-slate-950/40 px-4 py-3">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-white">{value}</p>
    </div>
  );
}

function ResourceTable({
  headers,
  rows,
  emptyMessage,
}: {
  headers: string[];
  rows: ReactNode[][];
  emptyMessage: string;
}) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-white/[0.06] bg-slate-950/60">
            {headers.map((header) => (
              <th
                key={header}
                className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-white/[0.04] last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2.5 text-slate-300">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CloudCostDetectorResults({ data }: CloudCostDetectorResultsProps) {
  const { summary, resources } = data;
  const collectedAt = new Date(data.collected_at).toLocaleString();

  return (
    <div className="panel-accent overflow-hidden">
      <div className="border-b border-white/[0.06] px-6 py-4">
        <p className="panel-subtitle mb-1">Resource Inventory</p>
        <h2 className="panel-title">
          {data.account.account_name ?? data.account.account_id} · {data.region}
        </h2>
        <p className="mt-1 text-xs text-slate-500">Collected at {collectedAt}</p>
        {data.notes.length > 0 && (
          <ul className="mt-3 space-y-1 text-xs text-amber-300/90">
            {data.notes.map((note) => (
              <li key={note}>• {note}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="p-6 space-y-8">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <SummaryCard label="EC2" value={summary.ec2_count} />
          <SummaryCard label="EBS" value={summary.ebs_count} />
          <SummaryCard label="VPC" value={summary.vpc_count} />
          <SummaryCard label="Load Balancers" value={summary.load_balancer_count} />
          <SummaryCard label="Security Groups" value={summary.security_group_count} />
        </div>

        <div>
          <h3 className="section-label mb-3">EC2 Instances ({summary.ec2_count})</h3>
          <ResourceTable
            headers={["Instance", "Type", "State", "Private IP", "Tags"]}
            emptyMessage="No EC2 instances in this region."
            rows={resources.ec2.map((instance) => [
              <div key={instance.instance_id}>
                <p className="font-mono text-xs">{instance.instance_id}</p>
                {instance.name && <p className="text-xs text-slate-500">{instance.name}</p>}
              </div>,
              instance.instance_type ?? "—",
              instance.state ?? "—",
              instance.private_ip ?? "—",
              Object.keys(instance.tags).length > 0
                ? Object.entries(instance.tags)
                    .map(([k, v]) => `${k}=${v}`)
                    .join(", ")
                : "—",
            ])}
          />
        </div>

        <div>
          <h3 className="section-label mb-3">EBS Volumes ({summary.ebs_count})</h3>
          <ResourceTable
            headers={["Volume", "Size", "Type", "State", "Attached To"]}
            emptyMessage="No EBS volumes in this region."
            rows={resources.ebs.map((volume) => [
              <span key={volume.volume_id} className="font-mono text-xs">
                {volume.volume_id}
              </span>,
              volume.size_gb != null ? `${volume.size_gb} GB` : "—",
              volume.volume_type ?? "—",
              volume.state ?? "—",
              volume.attached_instance_id ?? "—",
            ])}
          />
        </div>

        <div>
          <h3 className="section-label mb-3">Elastic IPs ({summary.elastic_ip_count})</h3>
          <ResourceTable
            headers={["Allocation ID", "Public IP", "Associated Instance"]}
            emptyMessage="No Elastic IPs in this region."
            rows={resources.elastic_ips.map((eip) => [
              <span key={eip.allocation_id} className="font-mono text-xs">
                {eip.allocation_id}
              </span>,
              eip.public_ip ?? "—",
              eip.associated_instance_id ?? "—",
            ])}
          />
        </div>

        <div>
          <h3 className="section-label mb-3">Load Balancers ({summary.load_balancer_count})</h3>
          <ResourceTable
            headers={["Name", "Type", "Scheme", "State"]}
            emptyMessage="No ALB/NLB load balancers in this region."
            rows={resources.load_balancers.map((lb, index) => [
              lb.name ?? "—",
              lb.type ?? "—",
              lb.scheme ?? "—",
              lb.state ?? "—",
            ])}
          />
        </div>

        <div>
          <h3 className="section-label mb-3">
            Auto Scaling Groups ({summary.auto_scaling_group_count})
          </h3>
          <ResourceTable
            headers={["Name", "Desired", "Current", "Instances"]}
            emptyMessage="No auto scaling groups in this region."
            rows={resources.auto_scaling_groups.map((asg) => [
              asg.auto_scaling_group_name,
              asg.desired_capacity ?? "—",
              asg.current_capacity ?? "—",
              String(asg.instance_ids.length),
            ])}
          />
        </div>
      </div>
    </div>
  );
}
