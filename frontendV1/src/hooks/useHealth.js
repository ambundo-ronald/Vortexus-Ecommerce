import { useCallback, useState } from "react";

import { healthApi } from "../api/health.api";

export function useHealth() {
  const [state, setState] = useState({ live: null, ready: null, loading: false, error: null });

  const refresh = useCallback(async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const [live, ready] = await Promise.all([healthApi.live(), healthApi.ready()]);
      setState({ live, ready, loading: false, error: null });
      return { live, ready };
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error }));
      throw error;
    }
  }, []);

  return { ...state, refresh };
}
