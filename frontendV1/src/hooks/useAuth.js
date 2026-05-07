import { useEffect } from "react";

import { useAuthStore } from "../store/auth.store";

let authBootstrapStarted = false;

export function useAuth({ auto = true } = {}) {
  const store = useAuthStore();

  useEffect(() => {
    if (!auto || store.initialized || authBootstrapStarted) return;
    authBootstrapStarted = true;
    void store.loadUser({ silent: true });
  }, [auto, store.initialized, store.loadUser]);

  return store;
}
