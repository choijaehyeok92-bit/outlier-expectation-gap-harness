'use client';

import { show, type Filter, type FilterGroup, type ScreeningSpec } from '@/lib/api';

function flatten(group: FilterGroup, depth = 0): { clause: Filter; depth: number; op: string }[] {
  const rows: { clause: Filter; depth: number; op: string }[] = [];
  for (const clause of group.clauses ?? []) {
    if ('op' in clause) rows.push(...flatten(clause as FilterGroup, depth + 1));
    else rows.push({ clause: clause as Filter, depth, op: group.op });
  }
  return rows;
}

/** The compiled spec, shown as it will execute — not as it was typed. */
export function SpecView({ spec }: { spec: ScreeningSpec }) {
  const rows = flatten(spec.filters);
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium">ScreeningSpec</span>
        <span className="chip">기준일 {spec.as_of_date}</span>
        <span className="chip">missing: {spec.missing_policy}</span>
        <span className="chip">limit {spec.limit}</span>
        {spec.requires_harness_run && <span className="chip">requires harness run</span>}
        {spec.source?.parser && <span className="chip">parser: {spec.source.parser.provider}</span>}
      </div>
      {spec.universe?.jurisdictions?.length ? (
        <div className="muted mt-2 text-xs">관할: {spec.universe.jurisdictions.join(', ')}</div>
      ) : null}
      {rows.length === 0 ? (
        <p className="muted mt-3 text-sm">적용 가능한 필터가 없다.</p>
      ) : (
        <table className="mt-3">
          <thead>
            <tr><th>Field</th><th>연산</th><th>임계값</th><th>단위</th><th>원문</th></tr>
          </thead>
          <tbody>
            {rows.map(({ clause }, index) => (
              <tr key={index}>
                <td><code>{clause.field}</code></td>
                <td>{clause.operator}</td>
                <td>{Array.isArray(clause.value) ? clause.value.join(', ') : show(clause.value)}</td>
                <td className="muted">{clause.unit ?? clause.currency ?? '-'}</td>
                <td className="muted">{clause.origin_text ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
