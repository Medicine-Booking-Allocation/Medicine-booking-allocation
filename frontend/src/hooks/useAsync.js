import { useCallback, useEffect, useState } from 'react'

/*
 * Tiny data-fetching hook.
 *   const { data, loading, error, reload } = useAsync(() => apiFn(filter), [filter])
 * `fetcher` returns a promise (API modules already resolve to data).
 * `deps` re-runs the fetch when a dependency changes; `reload()` forces a refetch.
 */
export function useAsync(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let active = true
    setState((s) => ({ ...s, loading: true, error: null }))
    Promise.resolve(fetcher())
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((e) =>
        active &&
        setState({
          data: null,
          loading: false,
          error: e?.response?.data?.error || e?.message || 'Something went wrong',
        })
      )
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])

  return { ...state, reload }
}
