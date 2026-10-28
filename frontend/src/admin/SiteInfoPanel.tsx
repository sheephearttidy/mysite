/**
 * 站点信息:9 项可配字段,前台全站生效。
 */
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import type { SiteInfo } from '@/lib/api';

const LABELS: Record<keyof SiteInfo, string> = {
  site_owner: '姓名',
  site_name: '站名',
  site_school: '学校',
  site_major: '专业',
  site_grade: '年级',
  site_focus: '方向 / 标签',
  site_slogan: '标语',
  site_credit: '版权后缀',
  site_start_year: '建站年份',
};

export function SiteInfoPanel({ onSaved }: { onSaved: () => void }) {
  const [info, setInfo] = useState<SiteInfo | null>(null);
  const [error, setError] = useState('');
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .get<SiteInfo>('/api/site')
      .then(setInfo)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : '加载失败'),
      );
  }, []);

  async function save() {
    if (!info) return;
    setBusy(true);
    setError('');
    setOk(false);
    try {
      const saved = await api.put<SiteInfo>('/api/site', info);
      setInfo(saved);
      setOk(true);
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '保存失败');
    } finally {
      setBusy(false);
    }
  }

  if (!info) {
    return <p style={{ color: 'var(--text-3)' }}>{error || '加载中…'}</p>;
  }

  return (
    <div>
      <h2 className="mb-4 font-round text-xl font-black">🏷️ 站点信息</h2>
      <p className="mb-4 text-xs" style={{ color: 'var(--text-3)' }}>
        改完保存,前台刷新即生效(导航、页脚、各页文案都用这里的值)
      </p>

      <div className="sticker">
        <div className="grid gap-3 sm:grid-cols-2">
          {(Object.keys(LABELS) as (keyof SiteInfo)[]).map((k) => (
            <div key={k}>
              <label className="block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
                {LABELS[k]}
              </label>
              <input
                value={info[k]}
                onChange={(e) => setInfo({ ...info, [k]: e.target.value })}
                className="mt-1 w-full rounded-lg border-2 px-2 py-1 text-sm outline-none"
                style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
              />
            </div>
          ))}
        </div>

        {error && <p className="mt-3 text-xs font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>}
        {ok && <p className="mt-3 text-xs font-bold" style={{ color: 'var(--teal)' }}>✅ 已保存</p>}

        <button type="button" className="btn btn-accent mt-4 text-sm" onClick={save} disabled={busy}>
          {busy ? '保存中…' : '保存'}
        </button>
      </div>
    </div>
  );
}
