/**
 * 来找我:联系方式 + 留言墙(多轮对话) + 匿名提问箱 + 友情链接。
 */
import { useState } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { api, ApiError } from '@/lib/api';
import type { Message, PageData, Question } from '@/lib/api';
import { useApi } from '@/lib/useApi';

const COLORS = ['pink', 'yellow', 'teal', 'purple', 'orange', 'blue'] as const;
const BG: Record<string, string> = {
  pink: 'var(--pink-bg)', yellow: 'var(--yellow-bg)', teal: 'var(--teal-bg)',
  purple: 'var(--purple-bg)', orange: 'var(--orange-bg)', blue: 'var(--blue-bg)',
};

function timeAgo(ts: number): string {
  const diff = Math.floor(Date.now() / 1000) - ts;
  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`;
  return new Date(ts * 1000).toLocaleDateString('zh-CN');
}

export default function Contact() {
  const page = useApi<PageData>('/api/page/contact');
  const messages = useApi<Message[]>('/api/messages');
  const questions = useApi<Question[]>('/api/questions');

  const [name, setName] = useState('');
  const [body, setBody] = useState('');
  const [color, setColor] = useState<(typeof COLORS)[number]>('pink');
  const [sending, setSending] = useState(false);
  const [tip, setTip] = useState<{ ok: boolean; text: string } | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const [qBody, setQBody] = useState('');
  const [qTip, setQTip] = useState<{ ok: boolean; text: string } | null>(null);

  const [followId, setFollowId] = useState<number | null>(null);
  const [followBody, setFollowBody] = useState('');

  async function submitMessage() {
    if (!body.trim()) return;
    setSending(true);
    setTip(null);
    try {
      const res = await api.post<{ id: number; token: string }>('/api/messages', {
        name: name.trim() || '匿名',
        body: body.trim(),
        color,
      });
      setToken(res.token);
      setBody('');
      setTip({ ok: true, text: '留言已提交,等站主审核后就会出现在墙上 ✅' });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : '提交失败,请稍后再试';
      setTip({ ok: false, text: msg });
    } finally {
      setSending(false);
    }
  }

  async function submitFollow() {
    if (!followId || !followBody.trim() || !token) return;
    try {
      await api.post(`/api/messages/${followId}/follow`, {
        token,
        body: followBody.trim(),
      });
      setFollowBody('');
      setFollowId(null);
      setTip({ ok: true, text: '追问已提交,审核后展示' });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : '提交失败';
      setTip({ ok: false, text: msg });
    }
  }

  async function submitQuestion() {
    if (!qBody.trim()) return;
    try {
      await api.post('/api/questions', { body: qBody.trim() });
      setQBody('');
      setQTip({ ok: true, text: '问题收到!等我回答后会公开在下面 ✅' });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : '提交失败';
      setQTip({ ok: false, text: msg });
    }
  }

  const site = page.data?.site;
  const links = page.data?.friendlinks ?? [];
  const msgs = messages.data ?? [];
  const qs = questions.data ?? [];

  return (
    <PageShell title="来找我玩" emoji="✉️" subtitle="留言、提问,或者只是路过">
      {/* 联系方式 */}
      <section className="mb-10 flex flex-wrap gap-3">
        <a href="https://github.com/sheephearttidy" target="_blank" rel="noopener noreferrer" className="btn">
          🐙 GitHub
        </a>
        <a href="mailto:hi@imyxj.xyz" className="btn">
          📧 邮件
        </a>
        {site && (
          <span className="btn" style={{ background: 'var(--teal-bg)' }}>
            📍 {site.site_school}
          </span>
        )}
      </section>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* 留言墙 */}
        <section>
          <h2 className="mb-4 font-round text-xl font-black">✉️ 留言墙</h2>

          <div className="sticker mb-5">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={20}
              placeholder="昵称(可不填)"
              className="w-full rounded-xl border-2 px-3 py-2 text-sm outline-none"
              style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
            />
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              maxLength={140}
              rows={3}
              placeholder="说点什么吧(最多 140 字)"
              className="mt-2 w-full resize-none rounded-xl border-2 px-3 py-2 text-sm outline-none"
              style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
            />
            <div className="mt-2 flex items-center gap-2">
              {COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  aria-label={`选择 ${c} 色`}
                  className="h-6 w-6 rounded-full border-2 transition-transform hover:scale-110"
                  style={{
                    background: BG[c],
                    borderColor: color === c ? 'var(--shadow)' : 'transparent',
                  }}
                />
              ))}
              <span className="ml-auto text-xs" style={{ color: 'var(--text-3)' }}>
                {body.length}/140
              </span>
              <button type="button" className="btn btn-accent" onClick={submitMessage} disabled={sending}>
                {sending ? '提交中…' : '发送'}
              </button>
            </div>
            {tip && (
              <p
                className="mt-2 text-xs font-bold"
                style={{ color: tip.ok ? 'var(--teal)' : '#d64545' }}
              >
                {tip.text}
              </p>
            )}
          </div>

          {messages.loading && <Loading />}
          {messages.error && <ErrorBox message={messages.error} />}
          {!messages.loading && msgs.length === 0 && <Empty text="还没有留言,来当第一个吧" />}

          <ul className="space-y-3">
            {msgs.map((m) => (
              <li key={m.id} className="rounded-sticker border-[3px] p-4" style={{ borderColor: 'var(--shadow)', background: BG[m.color] ?? 'var(--paper)' }}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-bold">{m.name}</span>
                  <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                    {timeAgo(m.ts)}
                  </span>
                </div>
                <p className="mt-1">{m.body}</p>

                {/* 对话线程 */}
                {m.threads.length > 0 && (
                  <ul className="mt-3 space-y-2 border-l-2 pl-3" style={{ borderColor: 'var(--rule)' }}>
                    {m.threads.map((t) => (
                      <li key={t.id} className="text-sm">
                        <span className="font-bold" style={{ color: t.role === 'owner' ? 'var(--pink)' : 'var(--text-2)' }}>
                          {t.role === 'owner' ? '站主' : m.name}:
                        </span>{' '}
                        {t.body}
                      </li>
                    ))}
                  </ul>
                )}

                {/* 凭凭证追问 */}
                {token && (
                  <div className="mt-2">
                    {followId === m.id ? (
                      <div className="flex gap-2">
                        <input
                          value={followBody}
                          onChange={(e) => setFollowBody(e.target.value)}
                          maxLength={140}
                          placeholder="继续追问…"
                          className="flex-1 rounded-lg border-2 px-2 py-1 text-sm outline-none"
                          style={{ borderColor: 'var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
                        />
                        <button type="button" className="btn px-3 py-1 text-xs" onClick={submitFollow}>
                          发送
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className="text-xs underline decoration-dotted"
                        style={{ color: 'var(--text-3)' }}
                        onClick={() => setFollowId(m.id)}
                      >
                        追问
                      </button>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>

        {/* 提问箱 + 友链 */}
        <section>
          <h2 className="mb-4 font-round text-xl font-black">💬 匿名提问箱</h2>
          <div className="sticker mb-5">
            <textarea
              value={qBody}
              onChange={(e) => setQBody(e.target.value)}
              maxLength={200}
              rows={3}
              placeholder="想问什么都可以(匿名,最多 200 字)"
              className="w-full resize-none rounded-xl border-2 px-3 py-2 text-sm outline-none"
              style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
            />
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                {qBody.length}/200
              </span>
              <button type="button" className="btn btn-accent ml-auto" onClick={submitQuestion}>
                提问
              </button>
            </div>
            {qTip && (
              <p className="mt-2 text-xs font-bold" style={{ color: qTip.ok ? 'var(--teal)' : '#d64545' }}>
                {qTip.text}
              </p>
            )}
          </div>

          {questions.loading && <Loading />}
          {!questions.loading && qs.length === 0 && <Empty text="还没有公开的问答" />}
          <ul className="space-y-3">
            {qs.map((q) => (
              <li key={q.id} className="sticker">
                <p className="font-bold">Q:{q.body}</p>
                <p className="mt-2 text-sm" style={{ color: 'var(--text-2)' }}>
                  A:{q.answer}
                </p>
              </li>
            ))}
          </ul>

          {links.length > 0 && (
            <>
              <h2 className="mb-4 mt-10 font-round text-xl font-black">🔗 友情链接</h2>
              <ul className="grid gap-3 sm:grid-cols-2">
                {links.map((l) => (
                  <li key={l.id}>
                    <a
                      href={l.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 rounded-xl border-[3px] px-3 py-2 transition-transform hover:-translate-y-0.5"
                      style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
                    >
                      <span className="text-xl">{l.emoji}</span>
                      <span className="min-w-0">
                        <span className="block truncate font-bold">{l.name}</span>
                        <span className="block truncate text-xs" style={{ color: 'var(--text-3)' }}>
                          {l.desc}
                        </span>
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>
    </PageShell>
  );
}
