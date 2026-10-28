/**
 * 后台登录页:密码 + 图形验证码。
 */
import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';

export default function AdminLogin({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState('');
  const [captcha, setCaptcha] = useState('');
  const [captchaUrl, setCaptchaUrl] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refreshCaptcha = () => {
    // 加时间戳绕过缓存
    setCaptchaUrl(`/api/captcha.svg?t=${Date.now()}`);
    setCaptcha('');
  };

  useEffect(() => {
    refreshCaptcha();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await api.post<{ ok: boolean; must_change: boolean }>('/api/login', {
        password,
        captcha,
      });
      if (res.ok) onSuccess();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : '登录失败';
      setError(msg);
      refreshCaptcha();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5" style={{ background: 'var(--cream)' }}>
      <form onSubmit={submit} className="sticker w-full max-w-sm">
        <h1 className="font-round text-2xl font-black">🔐 后台登录</h1>
        <p className="mt-1 text-xs" style={{ color: 'var(--text-3)' }}>
          输入密码和验证码
        </p>

        <label className="mt-5 block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
          密码
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          className="mt-1 w-full rounded-xl border-2 px-3 py-2 outline-none"
          style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
        />

        <label className="mt-4 block text-xs font-bold" style={{ color: 'var(--text-2)' }}>
          验证码
        </label>
        <div className="mt-1 flex gap-2">
          <input
            value={captcha}
            onChange={(e) => setCaptcha(e.target.value.toUpperCase())}
            maxLength={6}
            autoComplete="off"
            className="w-28 rounded-xl border-2 px-3 py-2 text-center font-mono tracking-widest outline-none"
            style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
          />
          <button
            type="button"
            onClick={refreshCaptcha}
            title="点击换一张"
            className="overflow-hidden rounded-xl border-2"
            style={{ borderColor: 'var(--rule)' }}
          >
            {captchaUrl && <img src={captchaUrl} alt="验证码" className="h-full w-[140px]" />}
          </button>
        </div>

        {error && (
          <p className="mt-3 text-xs font-bold" style={{ color: '#d64545' }}>
            ⚠️ {error}
          </p>
        )}

        <button type="submit" className="btn btn-accent mt-5 w-full" disabled={busy}>
          {busy ? '登录中…' : '登录'}
        </button>
      </form>
    </div>
  );
}
