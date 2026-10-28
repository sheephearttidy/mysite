/**
 * 数据备份:导出 JSON / 导入恢复 / 图片管理。
 */
import { useRef, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { useApi } from '@/lib/useApi';

interface UploadItem {
  file: string;
  path: string;
  size: number;
  mtime: number;
}

export function BackupPanel({ onRestored }: { onRestored: () => void }) {
  const uploads = useApi<UploadItem[]>('/api/admin/uploads');
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function doExport() {
    setBusy(true);
    setError('');
    try {
      const data = await api.get<Record<string, unknown>>('/api/admin/backup/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mysite-backup-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setMsg('导出成功');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '导出失败');
    } finally {
      setBusy(false);
    }
  }

  async function doImport(file: File) {
    if (!window.confirm('导入会清空现有内容并覆盖,确定继续?')) return;
    setBusy(true);
    setError('');
    setMsg('');
    try {
      const text = await file.text();
      const payload = JSON.parse(text);
      const res = await api.post<{ counts: Record<string, number> }>('/api/admin/backup/import', payload);
      setMsg(`导入完成:${JSON.stringify(res.counts)}`);
      onRestored();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '导入失败,请检查文件格式');
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  async function doUpload(file: File) {
    setBusy(true);
    setError('');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/admin/upload', { method: 'POST', body: form, credentials: 'same-origin' });
      if (!res.ok) throw new Error(`上传失败 (${res.status})`);
      const data = (await res.json()) as { path: string };
      setMsg(`上传成功:${data.path}`);
      uploads.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setBusy(false);
    }
  }

  async function doDelete(name: string) {
    if (!window.confirm(`删除 ${name}?`)) return;
    try {
      await api.del(`/api/admin/uploads/${encodeURIComponent(name)}`);
      uploads.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '删除失败');
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="font-round text-xl font-black">💾 数据备份</h2>

      {msg && <p className="text-xs font-bold" style={{ color: 'var(--teal)' }}>✅ {msg}</p>}
      {error && <p className="text-xs font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>}

      <div className="sticker">
        <h3 className="mb-2 font-bold">📤 导出 / 导入</h3>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn btn-accent text-sm" onClick={doExport} disabled={busy}>
            导出 JSON
          </button>
          <button
            type="button"
            className="btn text-sm"
            onClick={() => fileRef.current?.click()}
            disabled={busy}
          >
            选择 JSON 导入
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void doImport(f);
            }}
          />
        </div>
      </div>

      <div className="sticker">
        <h3 className="mb-2 font-bold">🖼️ 图片素材</h3>
        <input
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          className="text-sm"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void doUpload(f);
          }}
        />
        <p className="mt-2 text-xs" style={{ color: 'var(--text-3)' }}>
          支持 PNG / JPEG / GIF / WebP,单张不超过 8MB
        </p>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {(uploads.data ?? []).map((u) => (
            <div key={u.file} className="overflow-hidden rounded-lg border-2" style={{ borderColor: 'var(--rule)' }}>
              <img src={u.path} alt={u.file} loading="lazy" className="h-24 w-full object-cover" />
              <div className="p-1">
                <p className="truncate text-[10px]" title={u.file}>{u.file}</p>
                <button
                  type="button"
                  className="text-[10px] underline decoration-dotted"
                  style={{ color: '#d64545' }}
                  onClick={() => doDelete(u.file)}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
