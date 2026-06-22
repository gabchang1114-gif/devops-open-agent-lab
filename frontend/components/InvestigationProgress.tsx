"use client";

import { INVESTIGATION_STEPS, AWS_INVESTIGATION_STEPS } from "@/types/investigation";

interface InvestigationProgressProps {
  currentStep: string | null;
  progressPercentage: number;
  status: string;
  steps?: readonly string[];
  title?: string;
}

function stepState(
  step: string,
  currentStep: string | null,
  progressPercentage: number,
  status: string,
  steps: readonly string[],
): "complete" | "active" | "pending" {
  if (status === "failed") {
    const currentIndex = steps.findIndex((item) => item === currentStep);
    const stepIndex = steps.findIndex((item) => item === step);
    if (stepIndex <= currentIndex && currentIndex >= 0) {
      return stepIndex === currentIndex ? "active" : "complete";
    }
    return "pending";
  }

  const currentIndex = steps.findIndex((item) => item === currentStep);
  const stepIndex = steps.findIndex((item) => item === step);

  if (status === "success" || status === "partial_success" || status === "completed") {
    return "complete";
  }

  if (stepIndex < currentIndex) {
    return "complete";
  }
  if (step === currentStep) {
    return "active";
  }
  if (progressPercentage >= 100) {
    return "complete";
  }
  return "pending";
}

function StepIndicator({ state }: { state: "complete" | "active" | "pending" }) {
  if (state === "complete") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/15 text-[11px] text-emerald-400">
        ✓
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="relative flex h-6 w-6 shrink-0 items-center justify-center">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-500/25" />
        <span className="relative flex h-6 w-6 items-center justify-center rounded-full border border-brand-400/50 bg-brand-500/20 shadow-[0_0_12px_rgba(59,130,246,0.35)]">
          <span className="h-2 w-2 rounded-full bg-brand-400" />
        </span>
      </span>
    );
  }
  return (
    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-white/[0.08] bg-slate-800/80">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
    </span>
  );
}

export function InvestigationProgress({
  currentStep,
  progressPercentage,
  status,
  steps = INVESTIGATION_STEPS,
  title = "Investigating Cluster...",
}: InvestigationProgressProps) {
  const isRunning = status === "running" || status === "started";

  if (!isRunning && status !== "failed") {
    return null;
  }

  const isFailed = status === "failed";

  return (
    <div className="panel-accent animate-fade-in p-6">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="panel-subtitle mb-1">Investigation Progress</p>
          <h2 className="panel-title">
            {isFailed ? "Investigation Failed" : title}
          </h2>
          {currentStep && !isFailed && (
            <p className="mt-1.5 text-sm text-slate-400">
              Current step:{" "}
              <span className="font-medium text-slate-200">{currentStep}</span>
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold tabular-nums tracking-tight text-white">
            {progressPercentage}%
          </div>
          <div className="text-[11px] uppercase tracking-wider text-slate-500">Complete</div>
        </div>
      </div>

      <div className="mb-6 h-2 overflow-hidden rounded-full bg-slate-800/80 ring-1 ring-white/[0.04]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isFailed
              ? "bg-gradient-to-r from-red-600 to-red-400"
              : "bg-gradient-to-r from-brand-700 via-brand-500 to-brand-300 bg-[length:200%_100%] animate-shimmer"
          }`}
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      <ul className="space-y-0">
        {steps.map((step, index) => {
          const state = stepState(step, currentStep, progressPercentage, status, steps);
          const isLast = index === steps.length - 1;

          return (
            <li key={step} className="relative flex gap-3 pb-4 last:pb-0">
              {!isLast && (
                <span
                  className={`absolute left-3 top-7 h-[calc(100%-12px)] w-px ${
                    state === "complete" ? "bg-emerald-500/30" : "bg-white/[0.06]"
                  }`}
                  aria-hidden
                />
              )}
              <StepIndicator state={state} />
              <div className="min-w-0 pt-0.5">
                <span
                  className={`block text-sm leading-snug ${
                    state === "active"
                      ? "font-medium text-white"
                      : state === "complete"
                        ? "text-slate-300"
                        : "text-slate-500"
                  }`}
                >
                  {step}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
