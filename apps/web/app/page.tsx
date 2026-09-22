'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api, type Health, type Universe } from '@/lib/api';

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [universe, setUniverse] = useState<Universe | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.health(), api.universe()])
      .then(([h, u]) => {
        setHealth(h);
        setUniverse(u);
      })
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">투자 리서치 플랫폼</h1>
        <p className="muted mt-2 max-w-3xl text-sm">
          미국·한국 Universe 스크리닝 → 기존 Harness의 정량 판정 → 증거 연결 정성 딥다이브.
          현재 활성 백엔드는 완료된 하네스 run 인덱스이며, SEC/DART 전체 유니버스 적재는 Phase 3에서
          추가된다.
        </p>
      </section>

      {error && (
        <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>
          API에 연결하지 못했다: {error}
          <div className="muted mt-1">백엔드를 먼저 실행한다: <code>uvicorn apps.api.main:app --reload</code></div>
        </div>
      )}

      {health && universe && (
        <section className="grid gap-4 sm:grid-cols-3">
          <div className="card p-4">
            <div className="muted text-xs">완료된 하네스 run</div>
            <div className="mt-1 text-2xl">{universe.runs}</div>
          </div>
          <div className="card p-4">
            <div className="muted text-xs">관할별</div>
            <div className="mt-1 text-2xl">
              {Object.entries(universe.by_jurisdiction).map(([k, v]) => `${k} ${v}`).join(' · ')}
            </div>
          </div>
          <div className="card p-4">
            <div className="muted text-xs">최신 기준일</div>
            <div className="mt-1 text-2xl">{universe.latest_as_of_date ?? '미상'}</div>
          </div>
        </section>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          { href: '/screener', title: '1. Screener', body: '자연어 → ScreeningSpec → 결정론적 필터. LLM은 SQL을 쓰지 않는다.' },
          { href: '/runs', title: '2. Harness', body: '기존 하네스 결과를 읽는다. 점수는 재계산하지 않는다.' },
          { href: '/reports', title: '3. Deep Dive', body: '증거 연결 정성 보고서 + 독립 Red Team.' },
        ].map((card) => (
          <Link key={card.href} href={card.href} className="card block p-5 no-underline">
            <div className="font-medium" style={{ color: 'var(--text)' }}>{card.title}</div>
            <div className="muted mt-2 text-sm">{card.body}</div>
          </Link>
        ))}
      </section>

      {universe && <p className="muted text-xs">{universe.note}</p>}
    </div>
  );
}
