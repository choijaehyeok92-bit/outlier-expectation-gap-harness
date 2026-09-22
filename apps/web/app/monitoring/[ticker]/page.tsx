'use client';

/**
 * One company's watchlist, item by item.
 *
 * Items are grouped by what they ask of the reader rather than by source, so
 * a falsifier somebody recorded as triggered sits beside a KPI that breached
 * its threshold — both are "look at this now". `stale` and `never observed`
 * get their own group instead of being folded into ok, because the honest
 * summary of an unobserved watchlist is that nothing is known, not that
 * nothing is wrong.
 */
import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { MonitorStatusBadge } from '@/components/MonitorStatusBadge';
import { api, type DriftSeries, type MonitorItem, type MonitoringSnapshot } from '@/lib/api';

const GROUPS: { title: string; note: string; statuses: string[] }[] = [
  { title: '재검토 필요', note: '가설 파기 임계값을 넘었거나 falsifier가 발동했다. 판단은 여전히 사람과 IC의 몫이다.', statuses: ['thesis_break', 'triggered'] },
  { title: '경고', note: '경고 임계값을 넘었다. 재검토를 강제하지는 않는다.', statuses: ['warning'] },
  { title: '낡음', note: '선언된 주기 안에 관측이 없다. 괜찮다는 뜻이 아니라 아무도 보고 있지 않다는 뜻이다.', statuses: ['stale'] },
  { title: '한 번도 관측되지 않음', note: '감시하겠다고 선언했지만 아직 아무 기록이 없다.', statuses: ['unknown', 'unchecked'] },
  { title: '사람이 읽어야 함', note: '임계값이 산문이라 기계 비교가 불가능하다. 추측하지 않고 원문을 남긴다.', statuses: ['not_machine_checkable'] },
  { title: '임계값 안', note: '', statuses: ['ok', 'not_triggered'] },
];

function Item({ item }: { item: MonitorItem }) {
  return (
    <div className="border-t px-4 py-3" style={{ borderColor: 'var(--border)' }}>
      <div className="flex flex-wrap items-center gap-2">
        <MonitorStatusBadge status={item.status} />
        <span className="text-sm">{item.name}</span>
        <span className="muted text-xs">
          {item.source_kind}
          {item.source_ref ? `/${item.source_ref}` : ''} · {item.kind}
          {item.cadence ? ` · ${item.cadence}` : ''}
        </span>
      </div>
      {item.reason && <div className="muted mt-1 text-xs">{item.reason}</div>}
      {item.latest_observation ? (
        <div className="muted mt-1 text-xs">
          최근 관측 {String((item.latest_observation as Record<string, unknown>).as_of_date ?? '')} ·{' '}
          {String((item.latest_observation as Record<string, unknown>).source ?? '')}
        </div>
      ) : null}
    </div>
  );
}

export default function MonitoringCompanyPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const [data, setData] = useState<MonitoringSnapshot | null>(null);
  const [drift, setDrift] = useState<DriftSeries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.monitoringCompany(ticker).then(setData).catch((e) => setError(String(e.message)));
    api.monitoringDrift(ticker).then(setDrift).catch(() => setDrift(null));
  }, [ticker]);

  if (error) return <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>;
  if (!data) return <div className="muted text-sm">불러오는 중…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{data.ticker} Monitoring</h1>
        <p className="muted mt-2 text-sm">
          분석 기준일 {data.analysis_as_of_date ?? 'unknown'} · 평가일 {data.evaluated_as_of} · run{' '}
          <Link href={`/runs/${encodeURIComponent(data.run_id)}`} className="no-underline">{data.run_id}</Link>
          {data.deep_dive_id ? (
            <>
              {' '}· deep dive{' '}
              <Link href={`/deep-dive/${encodeURIComponent(data.deep_dive_id)}`} className="no-underline">
                {data.deep_dive_id}
              </Link>
            </>
          ) : null}
        </p>
      </div>

      <div className="card p-4 text-sm">
        <div className="flex flex-wrap gap-6">
          <div><div className="muted text-xs">감시 항목</div>{data.summary.items}</div>
          <div><div className="muted text-xs">재검토 필요</div>{data.summary.review_required}</div>
          <div><div className="muted text-xs">관측된 항목</div>{data.summary.observed}</div>
          <div><div className="muted text-xs">한 번도 관측 안 됨</div>{data.summary.never_observed}</div>
          <div><div className="muted text-xs">사람이 읽어야</div>{data.summary.not_machine_checkable}</div>
        </div>
      </div>

      {GROUPS.map((group) => {
        const items = data.items.filter((item) => group.statuses.includes(item.status));
        if (!items.length) return null;
        return (
          <div key={group.title} className="card">
            <div className="px-4 py-3">
              <div className="font-medium">{group.title} <span className="muted text-sm">({items.length})</span></div>
              {group.note && <div className="muted mt-1 text-xs">{group.note}</div>}
            </div>
            {items.map((item) => <Item key={item.watch_id} item={item} />)}
          </div>
        );
      })}

      {drift && drift.steps.length > 0 && (
        <div className="card">
          <div className="px-4 py-3">
            <div className="font-medium">Harness run 변화 <span className="muted text-sm">({drift.runs} runs)</span></div>
            <div className="muted mt-1 text-xs">{drift.reading_note}</div>
          </div>
          {drift.steps.map((step) => (
            <div key={`${step.from_run}-${step.to_run}`} className="border-t px-4 py-3 text-sm" style={{ borderColor: 'var(--border)' }}>
              <div className="flex flex-wrap items-center gap-2">
                <span>{step.from_run} → {step.to_run}</span>
                {step.comparable ? (
                  <span className="rounded px-2 py-0.5 text-xs" style={{ background: '#052e1b', color: '#4ade80' }}>비교 가능</span>
                ) : (
                  <span className="rounded px-2 py-0.5 text-xs" style={{ background: '#3b2f05', color: '#fbbf24' }}>정책이 바뀜 — 기업 변화로 읽지 말 것</span>
                )}
              </div>
              {step.not_comparable_reason && <div className="muted mt-1 text-xs">{step.not_comparable_reason}</div>}
              <div className="muted mt-2 text-xs">
                {step.changes.length === 0
                  ? '달라진 추적 필드 없음'
                  : step.changes.map((change) => `${change.field}: ${String(change.before)} → ${String(change.after)}`).join(' · ')}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card p-4 text-xs muted">
        <div className="mb-1 font-medium" style={{ color: 'var(--text)' }}>이 계층이 할 수 없는 것</div>
        {data.authority.may_not.join(' · ')}
        <div className="mt-2">{data.authority.statement}</div>
      </div>
    </div>
  );
}
