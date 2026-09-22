'use client';

/**
 * Credentials, entered here instead of in a file.
 *
 * This page is the only place in the app that sends a secret to the server,
 * and the boundary around it is deliberately narrow:
 *
 * **It is write-only.** No route returns a credential, so this page cannot
 * show you what is stored — only whether something is. An input is always
 * empty on load, and saving replaces rather than edits.
 *
 * **The server refuses a non-local caller.** If the API is reachable from a
 * network, `writable` comes back false with the reason, and the page says to
 * edit .env on that machine instead of posting a key to it.
 *
 * **Saving takes effect immediately.** The value goes into .env *and* the
 * running process, because a key that is saved and does not work until
 * somebody restarts is a difference nobody should have to know about.
 */
import { useEffect, useState } from 'react';
import { api, type Credential, type CredentialSettings } from '@/lib/api';

const GROUPS: { id: Credential['group']; title: string; blurb: string }[] = [
  { id: 'regulator', title: '규제기관', blurb: '0·1단계 — 명단과 Stage 0 적재. 둘 다 무료다.' },
  { id: 'market', title: '시세', blurb: '2단계 — 종가. polygon 무료 티어로 기준일 하나는 충분하다.' },
  { id: 'model', title: '모델', blurb: '5~7단계 — 비워 두면 유료 단계가 오프라인 스텁으로만 돌아 과금되지 않는다.' },
  { id: 'optional', title: '선택', blurb: '없어도 앱은 완전히 동작한다.' },
];

export default function SettingsPage() {
  const [data, setData] = useState<CredentialSettings | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [saved, setSaved] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const load = () => api.credentials().then(setData).catch((e) => setError(String(e.message)));
  useEffect(() => { load(); }, []);

  async function save(name: string, value: string) {
    setBusy(name);
    setError(null);
    try {
      const result = await api.setCredential(name, value);
      // The input is cleared rather than left holding the value: this page has
      // no reason to keep a secret in the DOM once the server has it.
      setDraft((prev) => ({ ...prev, [name]: '' }));
      setSaved((prev) => ({ ...prev, [name]: result.cleared ? '지웠다' : '저장됨' }));
      await load();
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(null);
    }
  }

  const Row = ({ row }: { row: Credential }) => {
    const value = draft[row.name] ?? '';
    const state = row.configured ? '설정됨'
      : row.needs_restart ? '파일에만 있음'
      : '없음';
    const colour = row.configured ? 'var(--accent)'
      : row.needs_restart ? '#fbbf24'
      : 'var(--muted)';
    return (
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-medium">{row.label}</span>
          <code className="muted text-xs">{row.name}</code>
          <span className="chip" style={{ color: colour }}>{state}</span>
          {saved[row.name] && <span className="chip" style={{ color: 'var(--accent)' }}>{saved[row.name]}</span>}
        </div>
        <p className="muted mt-1 text-xs">{row.unblocks}</p>
        <p className="muted mt-1 text-xs">{row.note}</p>
        {row.needs_restart && (
          <p className="mt-1 text-xs" style={{ color: '#fbbf24' }}>
            .env에는 있지만 실행 중인 API는 아직 읽지 않았다. 여기서 다시 저장하면 재시작 없이 반영된다.
          </p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input
            type={row.secret ? 'password' : 'text'}
            value={value}
            onChange={(e) => setDraft((prev) => ({ ...prev, [row.name]: e.target.value }))}
            placeholder={row.placeholder ?? (row.configured ? '새 값으로 교체하려면 입력' : '값을 붙여넣는다')}
            autoComplete="off"
            spellCheck={false}
            disabled={!data?.writable}
            className="flex-1 rounded-md bg-transparent px-2 py-1.5 text-sm"
            style={{ border: '1px solid var(--border)', minWidth: '16rem' }}
          />
          <button
            onClick={() => save(row.name, value)}
            disabled={!data?.writable || busy !== null || !value.trim()}
            className="rounded-md px-3 py-1.5 text-sm font-medium"
            style={{
              border: `1px solid ${value.trim() ? 'var(--accent)' : 'var(--border)'}`,
              color: value.trim() ? 'var(--accent)' : undefined,
              opacity: value.trim() ? 1 : 0.5,
            }}
          >
            {busy === row.name ? '저장 중…' : '저장'}
          </button>
          {(row.configured || row.in_file) && (
            <button
              onClick={() => save(row.name, '')}
              disabled={!data?.writable || busy !== null}
              className="rounded-md px-3 py-1.5 text-sm"
              style={{ border: '1px solid var(--border)' }}
            >
              지우기
            </button>
          )}
          {row.signup && (
            <a href={row.signup} target="_blank" rel="noreferrer" className="muted text-xs">발급 →</a>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="muted mt-2 text-sm">
          자격증명은 이 서버의 <code>.env</code>와 실행 중인 프로세스에만 들어간다. 저장하면
          <strong> 재시작 없이 즉시 반영</strong>된다. <strong>어떤 라우트도 값을 돌려주지 않으므로</strong>
          이 화면은 저장된 값을 보여줄 수 없다 — 설정 여부만 보여준다. 입력칸은 항상 비어 있고,
          저장은 수정이 아니라 교체다.
        </p>
      </div>

      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}

      {data && !data.writable && (
        <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>
          <div className="font-medium">여기서는 저장할 수 없다</div>
          <p className="muted mt-1 text-xs">{data.not_writable_reason}</p>
          <p className="muted mt-2 text-xs">
            대신 그 기계에서 <code>python scripts/set_key.py NAME</code>을 쓰거나{' '}
            <code>{data.env_path}</code>를 직접 편집한다.
          </p>
        </div>
      )}

      {data && GROUPS.map((group) => {
        const rows = data.credentials.filter((row) => row.group === group.id);
        if (!rows.length) return null;
        return (
          <div key={group.id} className="space-y-3">
            <div>
              <h2 className="text-lg font-medium">{group.title}</h2>
              <p className="muted text-xs">{group.blurb}</p>
            </div>
            {rows.map((row) => <Row key={row.name} row={row} />)}
          </div>
        );
      })}

      {data && (
        <p className="muted text-xs">
          파일: <code>{data.env_path}</code> — 커밋되지 않는다(.gitignore). {data.note}{' '}
          API가 외부에 열려 있다면 <code>HARNESS_DISABLE_KEY_WRITES=1</code>로 이 화면의 저장을 완전히 끌 수 있다.
        </p>
      )}
    </div>
  );
}
