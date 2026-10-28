/**
 * 后台通用表格编辑器:列表 + 行内编辑 + 增删。
 * 所有内容面板共用一套逻辑。
 */
import { useState } from 'react';
import { api, ApiError } from '@/lib/api';

export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'emoji';

export interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  /** 列表里是否展示这一列 */
  inList?: boolean;
  width?: string;
}

interface CrudTableProps {
  kind: string;
  title: string;
  emoji: string;
  fields: FieldDef[];
  rows: Record<string, unknown>[];
  onReload: () => void;
}

const EMPTY: Record<string, unknown> = {};

export function CrudTable({ kind, title, emoji, fields, rows, onReload }: CrudTableProps) {
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);
  const [draft, setDraft] = useState<Record<string, unknown>>(EMPTY);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const startNew = () => {
    const init: Record<string, unknown> = {};
    for (const f of fields) {
      init[f.key] = f.type === 'number' ? 0 : '';
    }
    setDraft(init);
    setEditing({});
    setError('');
  };

  const startEdit = (row: Record<string, unknown>) => {
    setDraft({ ...row });
    setEditing(row);
    setError('');
  };

  async function save() {
    setBusy(true);
    setError('');
    try {
      const payload: Record<string, unknown> = {};
      for (const f of fields) {
        let v = draft[f.key];
        if (f.type === 'number') v = Number(v) || 0;
        payload[f.key] = v;
      }
      if (editing && editing.id) {
        await api.put(`/api/content/${kind}/${editing.id}`, payload);
      } else {
        await api.post(`/api/content/${kind}`, payload);
      }
      setEditing(null);
      onReload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '保存失败');
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    if (!window.confirm('确定删除这一条?')) return;
    try {
      await api.del(`/api/content/${kind}/${id}`);
      onReload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '删除失败');
    }
  }

  const listFields = fields.filter((f) => f.inList !== false);

  return (
    <section>
      <div className="mb-4 flex items-center gap-3">
        <h2 className="font-round text-xl font-black">
          {emoji} {title}
          <span className="ml-2 text-sm font-normal" style={{ color: 'var(--text-3)' }}>
            {rows.length} 条
          </span>
        </h2>
        <button type="button" className="btn btn-accent ml-auto text-sm" onClick={startNew}>
          ＋ 新增
        </button>
      </div>

      {error && (
        <p className="mb-3 text-xs font-bold" style={{ color: 'var(--danger)' }}>⚠️ {error}</p>
      )}

      {/* 编辑表单 */}
      {editing && (
        <div className="sticker mb-5">
          <h3 className="mb-3 font-bold">{editing.id ? '编辑' : '新增'}</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {fields.map((f) => (
              <div key={f.key} className={f.type === 'textarea' ? 'sm:col-span-2' : ''}>
                <label className="admin-label">{f.label}</label>
                {f.type === 'textarea' ? (
                  <textarea
                    rows={2}
                    value={String(draft[f.key] ?? '')}
                    onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })}
                    className="admin-input mt-1 resize-none"
                  />
                ) : f.type === 'select' ? (
                  <select
                    value={String(draft[f.key] ?? '')}
                    onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })}
                    className="admin-input mt-1"
                  >
                    {(f.options ?? []).map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={f.type === 'number' ? 'number' : 'text'}
                    min={f.min}
                    max={f.max}
                    value={String(draft[f.key] ?? '')}
                    onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })}
                    className="admin-input mt-1"
                  />
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <button type="button" className="btn btn-accent text-sm" onClick={save} disabled={busy}>
              {busy ? '保存中…' : '保存'}
            </button>
            <button type="button" className="btn text-sm" onClick={() => setEditing(null)}>
              取消
            </button>
          </div>
        </div>
      )}

      {/* 列表 */}
      {rows.length === 0 ? (
        <p className="py-8 text-center text-sm" style={{ color: 'var(--text-3)' }}>
          还没有数据
        </p>
      ) : (
        <div
          className="overflow-x-auto rounded-sticker border-[3px]"
          style={{ borderColor: 'var(--shadow)' }}
        >
          <table className="admin-table">
            <thead>
              <tr>
                {listFields.map((f) => (
                  <th key={f.key}>{f.label}</th>
                ))}
                <th style={{ textAlign: 'right' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={String(row.id)}>
                  {listFields.map((f) => (
                    <td key={f.key} style={{ maxWidth: f.width ?? '240px' }}>
                      <span className="block truncate">{String(row[f.key] ?? '')}</span>
                    </td>
                  ))}
                  <td className="whitespace-nowrap" style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      className="text-xs underline decoration-dotted"
                      onClick={() => startEdit(row)}
                    >
                      编辑
                    </button>
                    <button
                      type="button"
                      className="ml-3 text-xs underline decoration-dotted"
                      style={{ color: 'var(--danger)' }}
                      onClick={() => remove(Number(row.id))}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
