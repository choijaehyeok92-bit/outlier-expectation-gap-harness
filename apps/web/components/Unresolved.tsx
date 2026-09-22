'use client';

import type { UnresolvedCondition } from '@/lib/api';

const REASON_KO: Record<string, string> = {
  no_mapped_field: '매핑된 field 없음',
  unsupported_operator: '지원하지 않는 연산자',
  backend_unavailable: '해당 데이터 백엔드 미가동',
  missing_fx_rate: '환율 미제공',
  ambiguous_threshold: '임계값 해석 불가',
  requires_harness_run: '하네스 실행 필요',
  unparsed_remainder: '사전에 없는 표현',
};

/**
 * Conditions the parser refused to guess at. Showing them is the point: a
 * screen that silently dropped "3년 매출 CAGR 15% 이상" would look like it had
 * answered the question it was asked.
 */
export function Unresolved({ rows }: { rows: UnresolvedCondition[] }) {
  if (!rows || rows.length === 0) return null;
  return (
    <div className="card p-4" style={{ borderColor: '#854d0e' }}>
      <div className="text-sm font-medium">해석되지 않아 적용하지 않은 조건 ({rows.length})</div>
      <p className="muted mt-1 text-xs">
        이 조건들은 결과에 반영되지 않았다. 추정으로 채우지 않는다.
      </p>
      <ul className="mt-3 space-y-2 text-sm">
        {rows.map((row, index) => (
          <li key={index}>
            <span className="chip mr-2">{REASON_KO[row.reason] ?? row.reason}</span>
            <span>{row.text}</span>
            {row.detail && <div className="muted mt-1 text-xs">{row.detail}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}
