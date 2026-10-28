/**
 * 互动审核:留言(含对话线程)、提问、涂鸦。
 */
import { useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { useApi } from '@/lib/useApi';

interface AdminMessage {
  id: number;
  name: string;
  body: string;
  color: string;
  ts: number;
  shown: number;
  ip: string;
  reply: string;
}

interface AdminQuestion {
  id: number;
  body: string;
  ts: number;
  shown: number;
  answer: string;
  ip: string;
}

const SHOWN_LABEL: Record<number, string> = { 0: '待审核', 1: '展示中', 2: '已隐藏' };

export function Moderation({ onChanged }: { onChanged: () => void }) {
  const [tab, setTab] = useState<'messages' | 'questions'>('messages');
  const messages = useApi<AdminMessage[]>('/api/messages/admin');
  const questions = useApi<AdminQuestion[]>('/api/questions/admin');
  const [error, setError] = useState('');
  const [answerDraft, setAnswerDraft] = useState<Record<number, string>>({});

  async function modMessage(id: number, action: string) {
    try {
      await api.post(`/api/messages/${id}/mod?action=${action}`);
      messages.reload();
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败');
    }
  }

  async function modQuestion(id: number, action: string, answer?: string) {
    try {
      const qs = new URLSearchParams({ action });
      if (answer) qs.set('answer', answer);
      await api.post(`/api/questions/${id}/mod?${qs.toString()}`);
      questions.reload();
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败');
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-2">
        <h2 className="font-round text-xl font-black">💬 互动审核</h2>
        <div className="ml-auto flex gap-2">
          <button
            type="button"
            className="pill"
            style={{ background: tab === 'messages' ? 'var(--yellow)' : 'var(--paper)' }}
            onClick={() => setTab('messages')}
          >
            留言 ({messages.data?.length ?? 0})
          </button>
          <button
            type="button"
            className="pill"
            style={{ background: tab === 'questions' ? 'var(--yellow)' : 'var(--paper)' }}
            onClick={() => setTab('questions')}
          >
            提问 ({questions.data?.length ?? 0})
          </button>
        </div>
      </div>

      {error && (
        <p className="mb-3 text-xs font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>
      )}

      {tab === 'messages' && (
        <div className="space-y-3">
          {(messages.data ?? []).length === 0 && (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>还没有留言</p>
          )}
          {(messages.data ?? []).map((m) => (
            <div key={m.id} className="sticker">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="font-bold">{m.name}</span>
                <span className="pill" style={{ background: m.shown === 0 ? 'var(--pink-bg)' : 'var(--teal-bg)' }}>
                  {SHOWN_LABEL[m.shown] ?? m.shown}
                </span>
                <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                  {new Date(m.ts * 1000).toLocaleString('zh-CN')} · {m.ip || '—'}
                </span>
              </div>
              <p className="mt-2">{m.body}</p>
              <div className="mt-2 flex gap-2">
                {m.shown !== 1 && (
                  <button type="button" className="btn px-3 py-1 text-xs" onClick={() => modMessage(m.id, 'approve')}>
                    通过
                  </button>
                )}
                {m.shown !== 2 && (
                  <button type="button" className="btn px-3 py-1 text-xs" onClick={() => modMessage(m.id, 'hide')}>
                    隐藏
                  </button>
                )}
                <button
                  type="button"
                  className="btn px-3 py-1 text-xs"
                  style={{ color: '#d64545' }}
                  onClick={() => modMessage(m.id, 'delete')}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'questions' && (
        <div className="space-y-3">
          {(questions.data ?? []).length === 0 && (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>还没有提问</p>
          )}
          {(questions.data ?? []).map((q) => (
            <div key={q.id} className="sticker">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="pill" style={{ background: q.answer ? 'var(--teal-bg)' : 'var(--pink-bg)' }}>
                  {q.answer ? '已回答' : '待回答'}
                </span>
                <span className="text-xs" style={{ color: 'var(--text-3)' }}>
                  {new Date(q.ts * 1000).toLocaleString('zh-CN')} · {q.ip || '—'}
                </span>
              </div>
              <p className="mt-2 font-bold">Q: {q.body}</p>
              {q.answer && <p className="mt-1 text-sm">A: {q.answer}</p>}

              <textarea
                rows={2}
                placeholder="写下回答,保存后即公开"
                value={answerDraft[q.id] ?? q.answer ?? ''}
                onChange={(e) => setAnswerDraft({ ...answerDraft, [q.id]: e.target.value })}
                className="mt-2 w-full resize-none rounded-lg border-2 px-2 py-1 text-sm outline-none"
                style={{ borderColor: 'var(--rule)', background: 'var(--cream)', color: 'var(--ink)' }}
              />
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  className="btn btn-accent px-3 py-1 text-xs"
                  onClick={() => modQuestion(q.id, 'approve', answerDraft[q.id])}
                >
                  保存并公开
                </button>
                <button type="button" className="btn px-3 py-1 text-xs" onClick={() => modQuestion(q.id, 'hide')}>
                  隐藏
                </button>
                <button
                  type="button"
                  className="btn px-3 py-1 text-xs"
                  style={{ color: '#d64545' }}
                  onClick={() => modQuestion(q.id, 'delete')}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
