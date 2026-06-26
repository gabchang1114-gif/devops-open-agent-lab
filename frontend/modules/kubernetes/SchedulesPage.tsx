"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { ClusterSelector } from "@/components/ClusterSelector";
import { useClusters, resolveDefaultCluster } from "@/hooks/useClusters";
import { useSchedules } from "@/hooks/useSchedules";
import type { InvestigationSchedule, InvestigationScheduleInput, ScheduleKind } from "@/types/schedule";
import {
  DAY_OF_WEEK_OPTIONS,
  SCHEDULE_KIND_OPTIONS,
} from "@/types/schedule";

const DEFAULT_FORM: InvestigationScheduleInput = {
  name: "",
  cluster_id: "",
  namespace: "",
  query: "",
  include_ai: true,
  schedule_kind: "daily",
  hour: 8,
  minute: 0,
  day_of_week: 1,
  cron_expression: "",
  timezone: "UTC",
  enabled: true,
};

function formatTimestamp(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function ScheduleForm({
  initial,
  onSubmit,
  onCancel,
  isSaving,
}: {
  initial?: InvestigationSchedule;
  onSubmit: (payload: InvestigationScheduleInput) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const clustersQuery = useClusters();
  const [form, setForm] = useState<InvestigationScheduleInput>(
    initial
      ? {
          name: initial.name,
          cluster_id: initial.cluster_id,
          namespace: initial.namespace ?? "",
          query: initial.query ?? "",
          include_ai: initial.include_ai,
          schedule_kind: initial.schedule_kind,
          hour: initial.hour,
          minute: initial.minute,
          day_of_week: initial.day_of_week,
          cron_expression: initial.cron_expression,
          timezone: initial.timezone,
          enabled: initial.enabled,
        }
      : DEFAULT_FORM,
  );

  useEffect(() => {
    if (!initial && clustersQuery.data?.clusters?.length && !form.cluster_id) {
      setForm((current) => ({
        ...current,
        cluster_id: resolveDefaultCluster(clustersQuery.data!.clusters),
      }));
    }
  }, [clustersQuery.data, form.cluster_id, initial]);

  const update = <K extends keyof InvestigationScheduleInput>(
    key: K,
    value: InvestigationScheduleInput[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async () => {
    await onSubmit({
      ...form,
      namespace: form.namespace?.trim() || null,
      query: form.query?.trim() || null,
      cron_expression:
        form.schedule_kind === "custom" ? form.cron_expression?.trim() || null : null,
    });
  };

  return (
    <div className="panel rounded-2xl p-6 sm:p-8">
      <h2 className="text-lg font-semibold text-white">
        {initial ? "Edit schedule" : "New proactive schedule"}
      </h2>
      <p className="mt-1 text-sm text-slate-400">
        Run Kubernetes investigations automatically on a recurring schedule. AI recommendations
        can still be delivered to Slack when enabled (at most once per hour to avoid alert fatigue).
      </p>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Schedule name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Nightly cluster health check"
              className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
            />
          </div>

          <ClusterSelector
            clusters={clustersQuery.data?.clusters ?? []}
            clusterId={form.cluster_id}
            onClusterChange={(value) => update("cluster_id", value)}
            loading={clustersQuery.isLoading}
            error={clustersQuery.error ? "Unable to load clusters" : null}
          />

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Namespace (optional)
            </label>
            <input
              type="text"
              value={form.namespace ?? ""}
              onChange={(e) => update("namespace", e.target.value)}
              placeholder="default"
              className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Focus query (optional)
            </label>
            <textarea
              value={form.query ?? ""}
              onChange={(e) => update("query", e.target.value)}
              placeholder="e.g. pods in CrashLoopBackOff"
              rows={3}
              className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
            />
          </div>

          <label className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-slate-900/50 px-4 py-3">
            <input
              type="checkbox"
              checked={form.include_ai}
              onChange={(e) => update("include_ai", e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 text-brand-500"
            />
            <span className="text-sm text-slate-200">Include AI diagnosis</span>
          </label>
        </div>

        <div className="space-y-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Frequency</label>
            <select
              value={form.schedule_kind}
              onChange={(e) => update("schedule_kind", e.target.value as ScheduleKind)}
              className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
            >
              {SCHEDULE_KIND_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs text-slate-500">
              {SCHEDULE_KIND_OPTIONS.find((o) => o.value === form.schedule_kind)?.description}
            </p>
          </div>

          {form.schedule_kind === "weekly" && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">Day of week</label>
              <select
                value={form.day_of_week}
                onChange={(e) => update("day_of_week", Number(e.target.value))}
                className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
              >
                {DAY_OF_WEEK_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {(form.schedule_kind === "daily" || form.schedule_kind === "weekly") && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Hour (UTC)</label>
                <input
                  type="number"
                  min={0}
                  max={23}
                  value={form.hour}
                  onChange={(e) => update("hour", Number(e.target.value))}
                  className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Minute</label>
                <input
                  type="number"
                  min={0}
                  max={59}
                  value={form.minute}
                  onChange={(e) => update("minute", Number(e.target.value))}
                  className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
                />
              </div>
            </div>
          )}

          {form.schedule_kind === "hourly" && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">
                Minute past the hour
              </label>
              <input
                type="number"
                min={0}
                max={59}
                value={form.minute}
                onChange={(e) => update("minute", Number(e.target.value))}
                className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 text-sm text-white outline-none focus:border-brand-500/40"
              />
            </div>
          )}

          {form.schedule_kind === "custom" && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300">
                Cron expression
              </label>
              <input
                type="text"
                value={form.cron_expression ?? ""}
                onChange={(e) => update("cron_expression", e.target.value)}
                placeholder="0 8 * * 1"
                className="w-full rounded-xl border border-white/[0.08] bg-slate-900/70 px-4 py-3 font-mono text-sm text-white outline-none focus:border-brand-500/40"
              />
              <p className="mt-2 text-xs text-slate-500">
                Standard 5-field cron: minute hour day month weekday (UTC)
              </p>
            </div>
          )}

          <label className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-slate-900/50 px-4 py-3">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => update("enabled", e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 text-brand-500"
            />
            <span className="text-sm text-slate-200">Schedule enabled</span>
          </label>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSaving || !form.name.trim() || !form.cluster_id}
          className="btn-primary"
        >
          {isSaving ? "Saving..." : initial ? "Save changes" : "Create schedule"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl border border-white/[0.1] px-5 py-2.5 text-sm font-medium text-slate-300 hover:text-white"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export function SchedulesPage() {
  const {
    schedules,
    isLoading,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    isSaving,
    isDeleting,
    saveError,
    deleteError,
  } = useSchedules();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<InvestigationSchedule | null>(null);

  const handleCreate = async (payload: InvestigationScheduleInput) => {
    await createSchedule(payload);
    setShowForm(false);
  };

  const handleUpdate = async (payload: InvestigationScheduleInput) => {
    if (!editing) return;
    await updateSchedule({ scheduleId: editing.id, payload });
    setEditing(null);
  };

  const handleToggle = async (schedule: InvestigationSchedule) => {
    await updateSchedule({
      scheduleId: schedule.id,
      payload: { enabled: !schedule.enabled },
    });
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Proactive Schedules</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Move from reactive troubleshooting to proactive monitoring. Schedule recurring
              Kubernetes investigations with AI diagnosis — results appear in Investigations and
              Slack alerts are limited to once per hour.
            </p>
          </div>
          {!showForm && !editing && (
            <button type="button" onClick={() => setShowForm(true)} className="btn-primary">
              New schedule
            </button>
          )}
        </div>

        {showForm && (
          <ScheduleForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            isSaving={isSaving}
          />
        )}

        {editing && (
          <ScheduleForm
            initial={editing}
            onSubmit={handleUpdate}
            onCancel={() => setEditing(null)}
            isSaving={isSaving}
          />
        )}

        {(saveError || deleteError) && (
          <p className="text-sm text-red-300">
            {(saveError as Error | undefined)?.message ||
              (deleteError as Error | undefined)?.message}
          </p>
        )}

        <div className="panel rounded-2xl p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">Your schedules</h3>

          {isLoading && <p className="text-sm text-slate-400">Loading schedules...</p>}

          {!isLoading && schedules.length === 0 && (
            <p className="text-sm text-slate-400">
              No schedules yet. Create one to run investigations automatically.
            </p>
          )}

          <div className="space-y-4">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className="rounded-xl border border-white/[0.08] bg-slate-900/40 p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-base font-semibold text-white">{schedule.name}</h4>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          schedule.enabled
                            ? "bg-emerald-500/15 text-emerald-300"
                            : "bg-slate-500/20 text-slate-400"
                        }`}
                      >
                        {schedule.enabled ? "Enabled" : "Paused"}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-slate-400">
                      Cluster <span className="text-slate-200">{schedule.cluster_id}</span>
                      {schedule.namespace ? ` · namespace ${schedule.namespace}` : ""}
                    </p>
                    <p className="mt-2 font-mono text-xs text-brand-200">{schedule.cron_expression}</p>
                    <div className="mt-3 grid gap-1 text-xs text-slate-500 sm:grid-cols-2">
                      <span>Next run: {formatTimestamp(schedule.next_run_at)}</span>
                      <span>Last run: {formatTimestamp(schedule.last_run_at)}</span>
                      {schedule.last_investigation_id && (
                        <span className="sm:col-span-2">
                          Last investigation:{" "}
                          <Link
                            href={`/investigations/${schedule.last_investigation_id}`}
                            className="text-brand-300 hover:text-brand-200"
                          >
                            {schedule.last_investigation_id.slice(0, 8)}…
                          </Link>
                          {schedule.last_status ? ` (${schedule.last_status})` : ""}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => handleToggle(schedule)}
                      disabled={isSaving}
                      className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white"
                    >
                      {schedule.enabled ? "Pause" : "Enable"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowForm(false);
                        setEditing(schedule);
                      }}
                      className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteSchedule(schedule.id)}
                      disabled={isDeleting}
                      className="rounded-lg border border-red-500/20 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/10"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
