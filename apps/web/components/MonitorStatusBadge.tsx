/**
 * A monitoring status, coloured by what it asks of the reader.
 *
 * Two of these are easy to get wrong in a UI and are deliberately not green.
 * `stale` means nobody has looked in longer than the declared cadence — that
 * is not a company doing fine, it is a company nobody is watching.
 * `not_machine_checkable` means the threshold is prose and no comparison was
 * made at all; showing it as anything reassuring would be a lie of omission.
 */
import type { MonitorStatus } from '@/lib/api';

const STYLE: Record<MonitorStatus, { bg: string; fg: string; label: string }> = {
  ok: { bg: '#052e1b', fg: '#4ade80', label: 'ok' },
  not_triggered: { bg: '#052e1b', fg: '#4ade80', label: 'not triggered' },
  warning: { bg: '#3b2f05', fg: '#facc15', label: 'warning' },
  stale: { bg: '#3b2f05', fg: '#fbbf24', label: 'stale' },
  thesis_break: { bg: '#450a0a', fg: '#f87171', label: 'thesis break' },
  triggered: { bg: '#450a0a', fg: '#f87171', label: 'falsifier triggered' },
  unknown: { bg: '#1f2937', fg: '#9ca3af', label: 'never observed' },
  unchecked: { bg: '#1f2937', fg: '#9ca3af', label: 'unchecked' },
  not_machine_checkable: { bg: '#1e1b4b', fg: '#a5b4fc', label: 'read by hand' },
};

export function MonitorStatusBadge({ status }: { status: MonitorStatus }) {
  const style = STYLE[status] ?? STYLE.unknown;
  return (
    <span
      className="inline-block rounded px-2 py-0.5 text-xs font-medium"
      style={{ background: style.bg, color: style.fg }}
    >
      {style.label}
    </span>
  );
}
