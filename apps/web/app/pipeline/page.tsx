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
import { api, type PipelineStatus, type PipelineStep, type StageProviders,
         type StageRunResult } from '@/lib/api';

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
  const [catalogue, setCatalogue] = useState<StageProviders | null>(null);
  // Per stage, because the offline stand-ins differ: `placeholder` analyses
  // nothing, `fixture` replays a recording, and offering the wrong one for a
  // stage produces a run that looks finished and contains nothing.
  const [providerFor, setProviderFor] = useState<Record<string, string>>({});
  const [modelFor, setModelFor] = useState<Record<string, string>>({});
  const [deepTicker, setDeepTicker] = useState('');
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [dryRun, setDryRun] = useState<Record<string, StageRunResult>>({});
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (date: string) => {
    try { setStatus(await api.pipeline(date)); } catch (e) { setError(String((e as Error).message)); }
  }, []);
  useEffect(() => { refresh(asOf); }, [refresh, asOf]);
  useEffect(() => {
    api.pipelineProviders()
      .then((payload) => {
        setCatalogue(payload);
        setProviderFor(Object.fromEntries(
          Object.entries(payload.stages).map(([id, set]) => [id, set.default])));
      })
      .catch(() => setCatalogue(null));
  }, []);

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

  const chosen = (id: string) =>
    catalogue?.stages[id]?.options.find((o) => o.name === providerFor[id]);

  async function paid(id: string, live: boolean) {
    setBusy(id); setError(null);
    try {
      const option = chosen(id);
      const model = modelFor[id]?.trim();
      const body = {
        as_of_date: asOf, dry_run: !live,
        provider: providerFor[id] ?? catalogue?.stages[id]?.default ?? 'placeholder',
        ...(option?.kind === 'api' && model ? { model } : {}),
      };
      const result = id === 'triage' ? await api.triage(body) : await api.fullHarness(body);
      setDryRun((prev) => ({ ...prev, [id]: result }));
      if (live) say(`${id}: ${body.provider}로 실행됨 — ${(result.results ?? []).length}건`);
    } catch (e) { setError(String((e as Error).message)); }
    finally { setBusy(null); await refresh(asOf); }
  }

  async function runDeepDive() {
    if (!deepTicker) { setError('종목을 고르지 않았다'); return; }
    setBusy('deep'); setError(null);
    try {
      const option = chosen('deep');
      const model = modelFor.deep?.trim();
      const r = await api.deepDiveRun(deepTicker, true,
                                      providerFor.deep ?? 'fixture',
                                      option?.kind === 'api' && model ? model : undefined);
      say(`deep: ${deepTicker} → ${r.deep_dive_id} (${providerFor.deep})`);
    } catch (e) { setError(String((e as Error).message)); }
    finally { setBusy(null); await refresh(asOf); }
  }

  /** The provider picker, model box and cost line shared by the paid stages. */
  const ProviderPicker = ({ id }: { id: string }) => {
    const set = catalogue?.stages[id];
    if (!set) return null;
    const option = chosen(id);
    return (
      <div className="mt-3 space-y-2">
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">공급자</span>
            <select
              value={providerFor[id] ?? set.default}
              onChange={(e) => setProviderFor((p) => ({ ...p, [id]: e.target.value }))}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)', color: 'var(--text)' }}
            >
              {set.options.map((o) => (
                <option key={o.name} value={o.name} style={{ background: 'var(--surface)' }}>
                  {o.name}{o.spends_money ? ' · 유료' : ' · 오프라인'}{o.configured ? '' : ' · 키 없음'}
                </option>
              ))}
            </select>
          </label>
          {option?.kind === 'api' && (
            <label className="flex flex-col gap-1">
              <span className="muted text-xs">모델 (비우면 기본값)</span>
              <input
                value={modelFor[id] ?? ''}
                onChange={(e) => setModelFor((p) => ({ ...p, [id]: e.target.value }))}
                placeholder={option.default_model ?? ''}
                className="rounded-md bg-transparent px-2 py-1"
                style={{ border: '1px solid var(--border)', minWidth: '11rem' }}
              />
            </label>
          )}
        </div>
        {option && <p className="muted text-xs">{option.note}</p>}
        {option && !option.configured && (
          <p className="text-xs" style={{ color: '#fbbf24' }}>
            서버에 <code>{option.env_var}</code>가 없어 지금 고르면 실패한다. 키는 API 프로세스의
            환경변수에 두고 재시작한다 — 브라우저로 전송되지 않으며 이 화면은 키를 알지 못한다.
          </p>
        )}
        {option?.spends_money && option.configured && (
          <p className="text-xs" style={{ color: '#fbbf24' }}>
            실제 모델이다. 기업당 {set.calls_per_company}콜이 그대로 과금된다.
            판정 계층은 영향받지 않는다 — 점수·archetype·Hard Veto·밸류에이션은 하네스가 계산한다.
            {catalogue?.model_note && ` ${catalogue.model_note}`}
          </p>
        )}
      </div>
    );
  };

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
                  {chosen(step.id)?.spends_money ? '유료 실행' : '실행'} — {eligible.length}개 × {step.calls_per_company}콜 = {eligible.length * (step.calls_per_company ?? 0)}콜
                </button>
              )}
            </>
          )}
          {step.id === 'deep' && (
            <>
              <select value={deepTicker} onChange={(e) => setDeepTicker(e.target.value)}
                      className="rounded-md bg-transparent px-2 py-1.5 text-sm"
                      style={{ border: '1px solid var(--border)', color: 'var(--text)' }}>
                <option value="" style={{ background: 'var(--surface)' }}>종목 선택…</option>
                {(step.eligible ?? []).map((ticker) => (
                  <option key={ticker} value={ticker} style={{ background: 'var(--surface)' }}>{ticker}</option>
                ))}
              </select>
              <button onClick={runDeepDive} disabled={busy !== null || !deepTicker}
                      className="rounded-md px-3 py-1.5 text-sm font-medium"
                      style={{ border: `1px solid ${deepTicker ? '#fbbf24' : 'var(--border)'}`,
                               color: deepTicker ? '#fbbf24' : undefined,
                               opacity: deepTicker ? 1 : 0.5 }}>
                {busy === 'deep' ? '작성 중…' : `보고서 작성 — ${step.calls_per_company}콜`}
              </button>
              <Link href="/reports" className="rounded-md px-3 py-1.5 text-sm no-underline"
                    style={{ border: '1px solid var(--border)', color: 'var(--text)' }}>
                보고서 보기 →
              </Link>
            </>
          )}
          <code className="muted text-xs">{step.action}</code>
        </div>

        {step.spends_money && <ProviderPicker id={step.id} />}

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
              공급자는 아래에서 고른다. 기본값은 오프라인 스텁이라 여기까지는 과금되지 않는다.
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
