/**
 * 数据获取 hook:统一 loading / error / 重试。
 */
import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';

interface State<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApi<T>(path: string | null) {
  const [state, setState] = useState<State<T>>({ data: null, loading: !!path, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!path) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));

    api
      .get<T>(path)
      .then((data) => {
        if (alive) setState({ data, loading: false, error: null });
      })
      .catch((err: unknown) => {
        if (!alive) return;
        const msg = err instanceof ApiError ? err.message : '网络错误,请稍后重试';
        setState({ data: null, loading: false, error: msg });
      });

    return () => {
      alive = false;
    };
  }, [path, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  return { ...state, reload };
}
