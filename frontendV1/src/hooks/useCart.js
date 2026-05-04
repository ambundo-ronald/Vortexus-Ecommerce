import { useEffect } from "react";

import { useCartStore } from "../store/cart.store";

export function useCart({ auto = true } = {}) {
  const store = useCartStore();

  useEffect(() => {
    if (auto) void store.hydrate();
    // hydrate once on component mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto]);

  return store;
}
