/**
 * 安全中心:安全设置 / 封锁名单 / 会话 / 审计日志。
 */
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { useApi } from '@/lib/useApi';

interface SecSettings {
  captcha: string;
  captcha_len: string;
  fail_threshold: string;
  block_minutes: string;
  session_hours: string;
  idle_minutes: string;
  audit_keep: string;
  pass_minlen: string;
  pass_classes: string;
  bind_ip: string;
}

interface SessionRow {
  sid: string;
  ip: string;
  ua: string;
  created: number;
  last_seen: number;
}

interface AuditRow {
  id: number;
  ts: number;
  ip: string;
  action: string;
  detail: string;
}

interface BlockedRow {
  ip: string;
  until: number;
  left_s: number;
}

type Tab = 'settings' | 'sessions' | 'blocked' | 'audit';

export function SecurityPanel() {
  const [tab, setTab] = useState<Tab>('settings');
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const settings = useApi<SecSettings>('/api/security/settings');
  const sessions = useApi<SessionRow[]>('/api/security/sessions');
  const blocked = useApi<BlockedRow[]>('/api/security/blocked');
  const audit = useApi<AuditRow[]>('/api/security/audit?limit=100');

  const [form, setForm] = useState<SecSettings | null>(null);
  useEffect(() => {
    if (settings.data) setForm(settings.data);
  }, [settings.data]);

  async function saveSettings() {
    if (!form) return;
    setError('');
    setMsg('');
    try {
      const saved = await api.post<SecSettings>('/api/security/settings', form);
      setForm(saved);
      setMsg('已保存');
      settings.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '保存失败');
    }
  }

  async function kickAll() {
    if (!window.confirm('踢掉其他所有登录会话?')) return;
    try {
      await api.post('/api/security/revoke-all');
      sessions.reload();
      setMsg('已踢掉其他会话');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败');
    }
  }

  async function unblock(ip: string) {
    try {
      await api.post(`/api/security/unblock?ip=${encodeURIComponent(ip)}`);
      blocked.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败');
    }
  }

  async function clearAudit() {
    if (!window.confirm('清空审计日志?')) return;
    try {
      await api.del('/api/security/audit');
      audit.reload();
      setMsg('审计日志已清空');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败');
    }
  }

  const TABS: { key: Tab; label: string; emoji: string }[] = [
    { key: 'settings', label: '安全设置', emoji: '⚙️' },
    { key: 'sessions', label: '登录会话', emoji: '💻' },
    { key: 'blocked', label: '封锁名单', emoji: '⛔' },
    { key: 'audit', label: '审计日志', emoji: '📜' },
  ];

  return (
    <div>
      <h2 className="mb-4 font-round text-xl font-black">🔐 安全中心</h2>

      <div className="mb-4 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className="pill"
            style={{ background: tab === t.key ? 'var(--yellow)' : 'var(--paper)' }}
          >
            {t.emoji} {t.label}
          </button>
        ))}
      </div>

      {msg && <p className="mb-3 text-xs font-bold" style={{ color: 'var(--teal)' }}>✅ {msg}</p>}
      {error && <p className="mb-3 text-xs font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>}

      {tab === 'settings' && form && (
        <div className="sticker">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field
              label="登录验证码"
              value={form.captcha}
              onChange={(v) => setForm({ ...form, captcha: v })}
              options={[{ value: '1', label: '开启' }, { value: '0', label: '关闭' }]}
            />
            <Field
              label="验证码位数(3~6)"
              value={form.captcha_len}
              onChange={(v) => setForm({ ...form, captcha_len: v })}
              type="number"
            />
            <Field
              label="失败几次封锁(1~50)"
              value={form.fail_threshold}
              onChange={(v) => setForm({ ...form, fail_threshold: v })}
              type="number"
            />
            <Field
              label="封锁时长 分钟(1~1440)"
              value={form.block_minutes}
              onChange={(v) => setForm({ ...form, block_minutes: v })}
              type="number"
            />
            <Field
              label="会话有效期 小时(1~720)"
              value={form.session_hours}
              onChange={(v) => setForm({ ...form, session_hours: v })}
              type="number"
            />
            <Field
              label="空闲登出 分钟(0=不登出)"
              value={form.idle_minutes}
              onChange={(v) => setForm({ ...form, idle_minutes: v })}
              type="number"
            />
            <Field
              label="审计保留条数(50~5000)"
              value={form.audit_keep}
              onChange={(v) => setForm({ ...form, audit_keep: v })}
              type="number"
            />
            <Field
              label="密码最小长度(6~64)"
              value={form.pass_minlen}
              onChange={(v) => setForm({ ...form, pass_minlen: v })}
              type="number"
            />
            <Field
              label="密码字符种类(1~4)"
              value={form.pass_classes}
              onChange={(v) => setForm({ ...form, pass_classes: v })}
              type="number"
            />
            <Field
              label="会话绑定 IP"
              value={form.bind_ip}
              onChange={(v) => setForm({ ...form, bind_ip: v })}
              options={[{ value: '1', label: '开启' }, { value: '0', label: '关闭' }]}
            />
          </div>
          <button type="button" className="btn btn-accent mt-4 text-sm" onClick={saveSettings}>
            保存设置
          </button>
        </div>
      )}

      {tab === 'sessions' && (
        <div className="sticker">
          <div className="mb-3 flex items-center">
            <span className="text-sm" style={{ color: 'var(--text-2)' }}>
              共 {sessions.data?.length ?? 0} 个活跃会话
            </span>
            <button type="button" className="btn ml-auto px-3 py-1 text-xs" onClick={kickAll}>
              踢掉其他会话
            </button>
          </div>
          <table className="w-full text-xs">
            <thead style={{ color: 'var(--text-3)' }}>
              <tr>
                <th className="py-1 text-left">会话</th>
                <th className="py-1 text-left">IP</th>
                <th className="py-1 text-left">设备</th>
                <th className="py-1 text-left">最后活动</th>
              </tr>
            </thead>
            <tbody>
              {(sessions.data ?? []).map((s) => (
                <tr key={s.sid} className="border-t" style={{ borderColor: 'var(--rule)' }}>
                  <td className="py-1 font-mono">{s.sid}</td>
                  <td className="py-1">{s.ip || '—'}</td>
                  <td className="max-w-[220px] truncate py-1">{s.ua || '—'}</td>
                  <td className="py-1">{new Date(s.last_seen * 1000).toLocaleString('zh-CN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'blocked' && (
        <div className="sticker">
          {(blocked.data ?? []).length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>当前没有封锁的 IP</p>
          ) : (
            <ul className="space-y-2">
              {(blocked.data ?? []).map((b) => (
                <li
                  key={b.ip}
                  className="flex items-center gap-3 rounded-lg border-2 px-3 py-2 text-sm"
                  style={{ borderColor: 'var(--rule)' }}
                >
                  <span className="font-mono">{b.ip}</span>
                  <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                    剩余 {Math.ceil(b.left_s / 60)} 分钟
                  </span>
                  <button
                    type="button"
                    className="btn ml-auto px-3 py-1 text-xs"
                    onClick={() => unblock(b.ip)}
                  >
                    解除
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {tab === 'audit' && (
        <div className="sticker">
          <div className="mb-3 flex items-center">
            <span className="text-sm" style={{ color: 'var(--text-2)' }}>
              最近 {audit.data?.length ?? 0} 条
            </span>
            <button
              type="button"
              className="btn ml-auto px-3 py-1 text-xs"
              style={{ color: '#d64545' }}
              onClick={clearAudit}
            >
              清空
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-xs">
              <thead style={{ color: 'var(--text-3)' }}>
                <tr>
                  <th className="py-1 text-left">时间</th>
                  <th className="py-1 text-left">动作</th>
                  <th className="py-1 text-left">IP</th>
                  <th className="py-1 text-left">详情</th>
                </tr>
              </thead>
              <tbody>
                {(audit.data ?? []).map((a) => (
                  <tr key={a.id} className="border-t" style={{ borderColor: 'var(--rule)' }}>
                    <td className="py-1">{new Date(a.ts * 1000).toLocaleString('zh-CN')}</td>
                    <td className="py-1 font-mono">{a.action}</td>
                    <td className="py-1">{a.ip || '—'}</td>
                    <td className="max-w-[260px] truncate py-1">{a.detail || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: 'text' | 'number';
  options?: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-xs font-bold" style={{ color: 'var(--text-2)' }}>{label}</label>
      {options ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="admin-input mt-1 w-full  border-2 px-2 py-1 text-sm outline-none"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="admin-input mt-1 w-full  border-2 px-2 py-1 text-sm outline-none"
        />
      )}
    </div>
  );
}
