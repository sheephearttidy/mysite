/**
 * 后台主应用:登录 → 强制改密 → 面板。
 *
 * 三道关卡:
 * 1. 未登录 → 登录页
 * 2. 已登录但 must_change → 改密页(不可跳过)
 * 3. 正常 → 后台面板
 *
 * 前端只是引导;真正拦住越权的是后端 require_admin(403 MUST_CHANGE_PASSWORD)。
 */
import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { useApi } from '@/lib/useApi';
import { useTheme } from '@/lib/theme';
import AdminLogin from './AdminLogin';
import { ForcePassword } from './ForcePassword';
import { CrudTable, type FieldDef } from './CrudTable';
import { Dashboard } from './Dashboard';
import { Moderation } from './Moderation';
import { SiteInfoPanel } from './SiteInfoPanel';
import { BackupPanel } from './BackupPanel';
import { SecurityPanel } from './SecurityPanel';

const COLOR_OPTS = [
  { value: 'pink', label: '粉' }, { value: 'yellow', label: '黄' },
  { value: 'teal', label: '青' }, { value: 'purple', label: '紫' },
  { value: 'orange', label: '橙' }, { value: 'blue', label: '蓝' },
];

const PANELS: { key: string; label: string; emoji: string }[] = [
  { key: 'dashboard', label: '数据看板', emoji: '📊' },
  { key: 'skills', label: '技能树', emoji: '🎯' },
  { key: 'timeline', label: '校园日常', emoji: '🗺️' },
  { key: 'stats', label: '趣味统计', emoji: '🧮' },
  { key: 'works', label: '项目墙', emoji: '🛠️' },
  { key: 'profile', label: '关于我', emoji: '🧍' },
  { key: 'honors', label: '荣誉墙', emoji: '🏆' },
  { key: 'notes', label: '随手记', emoji: '📝' },
  { key: 'friendlinks', label: '友情链接', emoji: '🔗' },
  { key: 'songs', label: '音乐', emoji: '🎵' },
  { key: 'photos', label: '相册', emoji: '📷' },
  { key: 'moderation', label: '互动审核', emoji: '💬' },
  { key: 'site', label: '站点信息', emoji: '🏷️' },
  { key: 'security', label: '安全中心', emoji: '🔐' },
  { key: 'backup', label: '数据备份', emoji: '💾' },
];

const FIELDS: Record<string, FieldDef[]> = {
  skills: [
    { key: 'name', label: '技能名', type: 'text' },
    { key: 'percent', label: '熟练度%', type: 'number', min: 0, max: 100 },
    { key: 'note', label: '吐槽', type: 'textarea' },
    { key: 'category', label: '分类', type: 'select', options: [
      { value: 'serious', label: '认真' }, { value: 'passive', label: '被动' },
    ]},
    { key: 'color', label: '颜色', type: 'select', options: COLOR_OPTS },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  timeline: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'time_label', label: '时间', type: 'text', width: '100px' },
    { key: 'title', label: '标题', type: 'text' },
    { key: 'content', label: '内容', type: 'textarea', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  stats: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'number', label: '数字', type: 'number' },
    { key: 'unit', label: '单位', type: 'text', width: '70px' },
    { key: 'label', label: '说明', type: 'text' },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  works: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'title', label: '项目名', type: 'text' },
    { key: 'cover', label: '封面色', type: 'select', options: COLOR_OPTS },
    { key: 'pill', label: '状态', type: 'text', width: '90px' },
    { key: 'desc', label: '描述', type: 'textarea', inList: false },
    { key: 'link', label: '链接', type: 'text', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  profile: [
    { key: 'kind', label: '类型', type: 'select', options: [
      { value: 'about', label: '段落' }, { value: 'info', label: '卡片' },
    ]},
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'label', label: '小标题', type: 'text' },
    { key: 'value', label: '内容', type: 'textarea' },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  honors: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'year', label: '年份', type: 'text', width: '90px' },
    { key: 'title', label: '奖项', type: 'text' },
    { key: 'level', label: '级别', type: 'select', options: [
      { value: 'national', label: '国家级' }, { value: 'provincial', label: '省级' },
      { value: 'school', label: '校级' }, { value: 'other', label: '其他' },
    ]},
    { key: 'desc', label: '说明', type: 'textarea', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  notes: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'text', label: '内容', type: 'text' },
    { key: 'mood', label: '底色', type: 'select', options: COLOR_OPTS },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  friendlinks: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'name', label: '站点名', type: 'text' },
    { key: 'url', label: '链接', type: 'text' },
    { key: 'desc', label: '介绍', type: 'textarea', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  songs: [
    { key: 'emoji', label: '图标', type: 'text', width: '60px' },
    { key: 'title', label: '歌名', type: 'text' },
    { key: 'artist', label: '歌手', type: 'text' },
    { key: 'song_id', label: 'QQ songid', type: 'text', width: '110px' },
    { key: 'note', label: '安利', type: 'textarea', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
  photos: [
    { key: 'file', label: '文件名', type: 'text' },
    { key: 'title', label: '标题', type: 'text' },
    { key: 'category', label: '分类', type: 'text', width: '90px' },
    { key: 'shot_at', label: '拍摄日期', type: 'text', width: '110px' },
    { key: 'shown', label: '展示', type: 'select', options: [
      { value: '1', label: '显示' }, { value: '0', label: '隐藏' },
    ]},
    { key: 'desc', label: '描述', type: 'textarea', inList: false },
    { key: 'sort', label: '排序', type: 'number', inList: false },
  ],
};

type Gate = 'checking' | 'login' | 'force-password' | 'ready';

export function AdminApp() {
  const [gate, setGate] = useState<Gate>('checking');
  const [panel, setPanel] = useState('dashboard');
  const [content, setContent] = useState<Record<string, unknown[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { isDark, toggle } = useTheme();

  const alerts = useApi<Record<string, number>>(
    gate === 'ready' ? '/api/admin/alerts' : null,
  );

  /** 判断当前该进哪一关 */
  const checkGate = useCallback(async () => {
    try {
      const me = await api.get<{ must_change: boolean }>('/api/me');
      setGate(me.must_change ? 'force-password' : 'ready');
    } catch {
      setGate('login');
    }
  }, []);

  useEffect(() => {
    void checkGate();
  }, [checkGate]);

  const reloadContent = useCallback(() => {
    setLoading(true);
    api
      .get<Record<string, unknown[]>>('/api/content')
      .then((d) => {
        setContent(d);
        setError('');
      })
      .catch((err: unknown) => {
        // 会话中途失效或状态变化,回到对应关卡
        if (err instanceof ApiError && (err.status === 403 || err.status === 401)) {
          void checkGate();
          return;
        }
        setError(err instanceof ApiError ? err.message : '加载失败');
      })
      .finally(() => setLoading(false));
  }, [checkGate]);

  useEffect(() => {
    if (gate === 'ready') reloadContent();
  }, [gate, reloadContent]);

  async function logout() {
    await api.post('/api/logout').catch(() => undefined);
    setGate('login');
  }

  if (gate === 'checking') {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ background: 'var(--cream)' }}
      >
        <span style={{ color: 'var(--text-3)' }}>检查登录态…</span>
      </div>
    );
  }

  if (gate === 'login') {
    return <AdminLogin onSuccess={checkGate} />;
  }

  if (gate === 'force-password') {
    return <ForcePassword onDone={checkGate} onLogout={logout} />;
  }

  const pending = alerts.data ?? {};
  const current = PANELS.find((p) => p.key === panel);

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--cream)' }}>
      {/* 侧边栏 */}
      <aside
        className="hidden w-56 shrink-0 flex-col border-r-[3px] md:flex"
        style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
      >
        <div className="border-b-2 px-4 py-4" style={{ borderColor: 'var(--rule)' }}>
          <p className="font-round font-black">🏠 我的小窝</p>
          <p className="text-xs" style={{ color: 'var(--text-3)' }}>SITE ADMIN</p>
        </div>
        <nav className="flex-1 overflow-y-auto p-2">
          {PANELS.map((p) => {
            const badge = pending[p.key];
            return (
              <button
                key={p.key}
                type="button"
                onClick={() => setPanel(p.key)}
                className="mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-bold transition-colors"
                style={{
                  background: panel === p.key ? 'var(--yellow)' : 'transparent',
                  color: panel === p.key ? 'var(--on-accent)' : 'var(--ink)',
                }}
              >
                <span>{p.emoji}</span>
                <span className="flex-1">{p.label}</span>
                {badge > 0 && (
                  <span
                    className="rounded-full px-1.5 text-[10px] font-black"
                    style={{ background: 'var(--pink)', color: '#fff' }}
                  >
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
        <div className="border-t-2 p-3" style={{ borderColor: 'var(--rule)' }}>
          <a href="/" className="block text-xs underline decoration-dotted">← 回前台</a>
          <button
            type="button"
            onClick={logout}
            className="mt-2 text-xs underline decoration-dotted"
            style={{ color: 'var(--danger)' }}
          >
            退出登录
          </button>
        </div>
      </aside>

      {/* 主区 */}
      <main className="min-w-0 flex-1 p-5">
        {/* 顶栏 */}
        <div className="mb-4 flex items-center gap-2">
          <span className="font-round text-sm font-black md:text-base">
            {current?.emoji} {current?.label}
          </span>
          <button
            type="button"
            onClick={toggle}
            aria-label={isDark ? '切换到亮色模式' : '切换到暗色模式'}
            className="btn ml-auto px-3 py-1.5 text-sm"
          >
            {isDark ? '☀️ 亮色' : '🌙 暗色'}
          </button>
          <button
            type="button"
            onClick={logout}
            className="btn px-3 py-1.5 text-sm md:hidden"
          >
            退出
          </button>
        </div>

        {/* 移动端面板切换 */}
        <div className="mb-4 md:hidden">
          <select
            value={panel}
            onChange={(e) => setPanel(e.target.value)}
            className="admin-input"
          >
            {PANELS.map((p) => (
              <option key={p.key} value={p.key}>
                {p.emoji} {p.label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <p className="mb-3 text-xs font-bold" style={{ color: 'var(--danger)' }}>
            ⚠️ {error}
          </p>
        )}
        {loading && <p className="text-sm" style={{ color: 'var(--text-3)' }}>加载中…</p>}

        {panel === 'dashboard' && <Dashboard />}
        {panel === 'moderation' && (
          <Moderation onChanged={() => { reloadContent(); alerts.reload(); }} />
        )}
        {panel === 'site' && <SiteInfoPanel onSaved={reloadContent} />}
        {panel === 'security' && <SecurityPanel />}
        {panel === 'backup' && <BackupPanel onRestored={reloadContent} />}

        {FIELDS[panel] && (
          <CrudTable
            kind={panel}
            title={current?.label ?? panel}
            emoji={current?.emoji ?? ''}
            fields={FIELDS[panel]}
            rows={(content[panel] as Record<string, unknown>[]) ?? []}
            onReload={reloadContent}
          />
        )}
      </main>
    </div>
  );
}
