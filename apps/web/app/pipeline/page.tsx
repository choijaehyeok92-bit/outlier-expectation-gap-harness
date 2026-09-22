'use client';

/**
 * The funnel as eight buttons.
 *
 * The order was always in the docs and the commands were always there; what
 * was missing was a place that says what is done and what is next. This is
 * that place, and it keeps one boundary visible above everything else.
 *
 * **Steps 0–4 are free. Steps 5–7 call a model once per agent per company.**
 * So the free ones sit behind a single chained button and the paid ones do
 * not: a "run everything" button is a button that spends money when somebody
 * clicks "next". Each paid step shows what it would cost, runs a dry run
 * first, and needs a second, separate press to actually start.
 *
 * Nothing here decides anything. The harness produces the score, the
 * archetype, the Hard Veto and the IC state; this page presses its buttons in
 * order and reports what came back.
 */
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { api, type PipelineStatus, type PipelineStep, type StageRunResult } from '@/lib/api';

const CHAINABLE = ['universe', 'market', 'warehouse', 'screen'];
const DEFAULT_QUERY = '순현금이고 hard veto 통과, 코어 점수 70 이상';

const STATE_LABEL: Record<string, string> = {
  done: '완료', partial: '일부', todo: '해야 함', blocked: '막힘',
};
const STATE_COLOR: Record<string, string> = {
  done: 'var(--accent)', partial: '#fbbf24', todo: 'var(--muted)', blocked: '#f87171',
};

export default function PipelinePage() {
  const [asOf, setAsOf] = useState('2026-09-21');
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [dryRun, setDryRun] = useState<Record<string, StageRunResult>>({});
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (date: string) => {
    try { setStatus(await api.pipeline(date)); } catch (e) { setError(String((e as Error).message)); }
  }, []);
  useEffect(() => { refresh(asOf); }, [refresh, asOf]);

  const say = (line: string) => setLog((prev) => [...prev, line]);

  async function runStep(id: string): Promise<string> {
    if (id === 'universe') {
      const r = await api.universeSync({ markets: ['US', 'KR'], as_of_date: asOf });
      return `명단 ${r.summary.included}종목 (제외 ${r.summary.excluded})`;
    }
    if (id === 'market') {
      const r = await api.marketFetch({ as_of_date: asOf, scope: 'packs' });
      return `${r.session_date} 세션 · ${r.written_count}종목 기록`
        + (r.missing_price.length ? ` · 시세 없음 ${r.missing_price.length}` : '');
    }
    if (id === 'warehouse') {
      const r = await api.warehouseBuild(asOf);
      return `지표 창고 ${r.companies}종목`;
    }
    if (id === 'screen') {
      const r = await api.screen({ text: query, as_of_date: asOf, persist: true });
      return `${r.screen_run_id} · ${r.summary.matched_count}/${r.summary.considered} 통과`;
    }
    throw new Error(`${id}는 이 버튼으로 실행하지 않는다`);
  }

  async function one(id: string) {
    setBusy(id); setError(null);
    try { say(`${id}: ${await runStep(id)}`); } catch (e) { setError(String((e as Error).message)); }
    finally { setBusy(null); await refresh(asOf); }
  }

  async function chain() {
    setBusy('chain'); setError(null); setLog([]);
    const steps = (status?.steps ?? []).filter((s) => CHAINABLE.includes(s.id) && s.state !== 'done');
    if (!steps.length) { say('무료 구간은 이미 끝나 있다.'); setBusy(null); return; }
    for (const step of steps) {
      try { say(`${step.id}: ${await runStep(step.id)}`); }
      catch (e) {
        // Stop rather than press on. Building the warehouse anyway would use
        // whatever prices happen to be on disk for a session the operator
        // asked to refresh — a quiet substitution, which is exactly what this
        // repository does not do. The remaining steps stay one click away.
        say(`${step.id}: 멈춤 — ${(e as Error).message}`);
        const left = steps.slice(steps.indexOf(step) + 1).map((s) => s.title);
        if (left.length) say(`남은 단계는 개별 버튼으로 돌릴 수 있다: ${left.join(' → ')}`);
        break;
      }
    }
    setBusy(null); await refresh(asOf);
  }

  async function paid(id: string, live: boolean) {
    setBusy(id); setError(null);
    try {
      const body = { as_of_date: asOf, dry_run: !live, ...(live ? { provider: 'placeholder' } : {}) };
      const result = id === 'triage' ? await api.triage(body) : await api.fullHarness(body);
      setDryRun((prev) => ({ ...prev, [id]: result }));
      if (live) say(`${id}: 실행됨 — ${(result.results ?? []).length}건`);
    } catch (e) { setError(String((e as Error).message)); }
    finally { setBusy(null); await refresh(asOf); }
  }

  const cred = status?.credentials ?? [];
  const missing = cred.filter((c) => !c.configured);

  const StepCard = ({ step, index }: { step: PipelineStep; index: number }) => {
    const isNext = status?.next_step === step.id;
    const plan = dryRun[step.id];
    const eligible = plan?.eligible ?? [];
    return (
      <div className="card p-4" style={isNext ? { borderColor: 'var(--accent)' } : undefined}>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="muted">{index}</span>
          <span className="font-medium">{step.title}</span>
          <span className="chip" style={{ color: STATE_COLOR[step.state] }}>{STATE_LABEL[step.state]}</span>
          {step.spends_money && (
            <span className="chip" style={{ color: '#fbbf24' }}>
              유료 · 기업당 {step.calls_per_company}콜
            </span>
          )}
          {isNext && <span className="chip" style={{ color: 'var(--accent)' }}>다음 할 일</span>}
        </div>
        <p className="muted mt-1 text-xs">{step.what}</p>
        <p className="mt-1 text-xs">{step.detail}</p>
        {step.blocked && step.state !== 'done' && (
          <p className="mt-1 text-xs" style={{ color: '#fbbf24' }}>막힘: {step.blocked}</p>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {CHAINABLE.includes(step.id) && (
            <button onClick={() => one(step.id)} disabled={busy !== null}
                    className="rounded-md px-3 py-1.5 text-sm"
                    style={{ border: '1px solid var(--border)' }}>
              {busy === step.id ? '실행 중…' : '이 단계 실행'}
            </button>
          )}
          {step.id === 'intake' && (
            <Link href="/universe" className="rounded-md px-3 py-1.5 text-sm no-underline"
                  style={{ border: '1px solid var(--border)', color: 'var(--text)' }}>
              적재할 기업 고르기 →
            </Link>
          )}
          {step.spends_money && step.id !== 'deep' && (
            <>
              <button onClick={() => paid(step.id, false)} disabled={busy !== null}
                      className="rounded-md px-3 py-1.5 text-sm"
                      style={{ border: '1px solid var(--border)' }}>
                {busy === step.id ? '확인 중…' : '예상 대상 보기 (dry run)'}
              </button>
              {plan && (
                <button onClick={() => paid(step.id, true)}
                        disabled={busy !== null || !eligible.length}
                        className="rounded-md px-3 py-1.5 text-sm font-medium"
                        style={{ border: `1px solid ${eligible.length ? '#fbbf24' : 'var(--border)'}`,
                                 color: eligible.length ? '#fbbf24' : undefined,
                                 opacity: eligible.length ? 1 : 0.5 }}>
                  실행 — {eligible.length}개 × {step.calls_per_company}콜 = {eligible.length * (step.calls_per_company ?? 0)}콜
                </button>
              )}
            </>
          )}
          {step.id === 'deep' && (
            <Link href="/reports" className="rounded-md px-3 py-1.5 text-sm no-underline"
                  style={{ border: '1px solid var(--border)', color: 'var(--text)' }}>
              보고서 보기 →
            </Link>
          )}
          <code className="muted text-xs">{step.action}</code>
        </div>

        {plan && (
          <div className="mt-2 text-xs">
            <p className="muted">
              대상 {eligible.length}개
              {(plan.not_eligible ?? []).length > 0 && ` · 제외 ${(plan.not_eligible ?? []).length}개`}
            </p>
            {eligible.length > 0 && (
              <p className="mt-1">{eligible.map((r) => r.ticker ?? r.run_id).join(', ')}</p>
            )}
            {eligible.length === 0 && (plan.not_eligible ?? []).length > 0 && (
              <p className="muted mt-1">
                제외 사유 예: {(plan.not_eligible ?? [])[0]?.reason}
              </p>
            )}
            <p className="muted mt-1">
              실행은 오프라인 placeholder 공급자로 돈다 — 실제 모델은 CLI에서{' '}
              <code>--provider openai</code>로 명시한다. 큐에 한 줄 넣는 것만으로 돈이 나가면 안 된다.
            </p>
          </div>
        )}
        {step.id === 'deep' && (step.eligible?.length ?? 0) > 0 && (
          <p className="muted mt-2 text-xs">자동 선정 통과: {step.eligible?.join(', ')}</p>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Pipeline</h1>
        <p className="muted mt-2 text-sm">
          명단 → 적재 → 시세 → 지표 → 정량 스크리닝 → triage → 전체 하네스 → 심층 보고서.
          <strong> 0~4단계는 무료</strong>라 한 번에 묶어 돌리고, <strong>5단계부터는 기업당
          에이전트마다 모델을 부르므로</strong> 묶지 않는다. 점수·archetype·Hard Veto·IC는
          하네스가 정한다 — 이 화면은 순서대로 버튼을 누를 뿐이다.
        </p>
      </div>

      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}

      <div className="card space-y-3 p-4">
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">기준일</span>
            <input value={asOf} onChange={(e) => setAsOf(e.target.value)}
                   className="rounded-md bg-transparent px-2 py-1"
                   style={{ border: '1px solid var(--border)' }} />
          </label>
          <label className="flex flex-1 flex-col gap-1" style={{ minWidth: '18rem' }}>
            <span className="muted text-xs">스크리닝 조건 (5단계에서 쓴다)</span>
            <input value={query} onChange={(e) => setQuery(e.target.value)}
                   className="rounded-md bg-transparent px-2 py-1"
                   style={{ border: '1px solid var(--border)' }} />
          </label>
          <button onClick={chain} disabled={busy !== null}
                  className="rounded-md px-3 py-1.5 font-medium"
                  style={{ border: '1px solid var(--accent)', color: 'var(--accent)' }}>
            {busy === 'chain' ? '실행 중…' : '무료 구간 한 번에'}
          </button>
          <button onClick={() => refresh(asOf)} disabled={busy !== null}
                  className="rounded-md px-3 py-1.5" style={{ border: '1px solid var(--border)' }}>
            상태 새로고침
          </button>
        </div>
        <p className="muted text-xs">
          무료 구간은 명단·시세·지표·스크리닝이다. <strong>적재(1단계)는 묶지 않는다</strong> —
          어느 기업을 적재할지는 사람이 고르는 결정이다. 한 단계가 실패하면 거기서 멈춘다:
          절반만 만들어진 입력을 다음 단계가 읽으면 아무도 되짚을 수 없는 숫자가 나온다.
        </p>
        {missing.length > 0 && (
          <p className="text-xs" style={{ color: '#fbbf24' }}>
            없는 자격증명: {missing.map((c) => c.env_var).join(', ')} — 해당 단계는 실패하고 이유를 말한다.
            키는 API 프로세스의 환경변수에 두고 재시작한다.
          </p>
        )}
      </div>

      {status && (
        <>
          <div className="card p-4 text-xs muted">{status.money_note}</div>
          <div className="space-y-3">
            {status.steps.map((step, i) => <StepCard key={step.id} step={step} index={i} />)}
          </div>
        </>
      )}

      {log.length > 0 && (
        <div className="card p-4">
          <div className="text-sm font-medium">실행 기록</div>
          <ul className="mt-2 space-y-1 text-xs">
            {log.map((line, i) => <li key={i} className="muted">{line}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
