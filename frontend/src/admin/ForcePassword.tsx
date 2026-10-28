/**
 * 强制改密页:首次登录必须改密才能进后台。
 *
 * 后端在 require_admin 里用 403 + MUST_CHANGE_PASSWORD 强制拦截,
 * 这里只负责引导;即便有人绕过前端,接口依然拒绝。
 */
import { useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { Aurora } from '@/components/Aurora';
import { GradientText } from '@/components/GradientText';

interface ForcePasswordProps {
  onDone: () => void;
  onLogout: () => void;
}

export function ForcePassword({ onDone, onLogout }: ForcePasswordProps) {
  const [oldPwd, setOldPwd] = useState('admin');
  const [newPwd, setNewPwd] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // 实时提示:长度 / 字符种类
  const hasLen = newPwd.length >= 8;
  const classes =
    (/[a-z]/.test(newPwd) ? 1 : 0) +
    (/[A-Z]/.test(newPwd) ? 1 : 0) +
    (/\d/.test(newPwd) ? 1 : 0) +
    (/[^a-zA-Z0-9]/.test(newPwd) ? 1 : 0);
  const hasClasses = classes >= 2;
  const matches = newPwd.length > 0 && newPwd === confirm;
  const canSubmit = hasLen && hasClasses && matches && newPwd.toLowerCase() !== 'admin';

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError('');
    try {
      await api.post('/api/password', { old: oldPwd, new: newPwd });
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '修改失败');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="relative flex min-h-screen items-center justify-center overflow-hidden px-5"
      style={{ background: 'var(--cream)' }}
    >
      <Aurora opacity={0.3} />

      <form onSubmit={submit} className="sticker relative w-full max-w-md">
        <h1 className="font-round text-2xl font-black">
          <GradientText duration={5}>🔐 首次登录,请修改密码</GradientText>
        </h1>
        <p className="mt-2 text-xs" style={{ color: 'var(--text-2)' }}>
          初始密码是 <code className="font-bold">admin</code>,为了站点安全,必须先改掉才能进入后台。
        </p>

        <label className="mt-5 block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
          当前密码
        </label>
        <input
          type="password"
          value={oldPwd}
          onChange={(e) => setOldPwd(e.target.value)}
          autoComplete="current-password"
          className="admin-input mt-1 w-full  border-2 px-3 py-2 outline-none"
        />

        <label className="mt-4 block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
          新密码
        </label>
        <input
          type="password"
          value={newPwd}
          onChange={(e) => setNewPwd(e.target.value)}
          autoComplete="new-password"
          className="admin-input mt-1 w-full  border-2 px-3 py-2 outline-none"
        />

        <label className="mt-4 block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
          再输一次
        </label>
        <input
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
          className="admin-input mt-1 w-full  border-2 px-3 py-2 outline-none"
        />

        {/* 规则清单 */}
        <ul className="mt-4 space-y-1 text-xs">
          <Rule ok={hasLen} text="至少 8 位" />
          <Rule ok={hasClasses} text="包含至少 2 类字符(大小写 / 数字 / 符号)" />
          <Rule ok={matches} text="两次输入一致" />
          <Rule ok={newPwd.length > 0 && newPwd.toLowerCase() !== 'admin'} text="不能还是 admin" />
        </ul>

        {error && (
          <p className="mt-3 text-xs font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>
        )}

        <button type="submit" className="btn btn-accent mt-5 w-full" disabled={busy || !canSubmit}>
          {busy ? '提交中…' : '修改并进入后台'}
        </button>

        <button
          type="button"
          onClick={onLogout}
          className="mt-3 w-full text-xs underline decoration-dotted"
          style={{ color: 'var(--text-3)' }}
        >
          退出登录
        </button>
      </form>
    </div>
  );
}

function Rule({ ok, text }: { ok: boolean; text: string }) {
  return (
    <li className="flex items-center gap-2" style={{ color: ok ? 'var(--teal)' : 'var(--text-3)' }}>
      <span>{ok ? '✓' : '○'}</span>
      {text}
    </li>
  );
}
