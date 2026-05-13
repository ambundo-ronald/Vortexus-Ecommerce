import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { wishlistApi } from "../../api/wishlist.api";
import WishlistCard from "../../components/wishlist/WishlistCard.jsx";
import Alert from "../../components/ui/Alert.jsx";
import EmptyState from "../../components/ui/EmptyState.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useUiStore } from "../../store/ui.store";
import { useWishlistStore } from "../../store/wishlist.store";
import { normalizeApiError } from "../../utils/errorHandler";
import "./wishlistManager.css";

export default function WishlistPage() {
  const notify = useUiStore((state) => state.notify);
  const setStatus = useWishlistStore((state) => state.setStatus);
  const [wishlists, setWishlists] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [wishlist, setWishlist] = useState(null);
  const [newListName, setNewListName] = useState("");
  const [editingName, setEditingName] = useState("");
  const [editingVisibility, setEditingVisibility] = useState("Private");
  const [shareLink, setShareLink] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const items = wishlist?.items || [];
  const moveTargets = useMemo(
    () => wishlists.filter((list) => String(list.id) !== String(wishlist?.id)),
    [wishlists, wishlist?.id]
  );

  const loadWishlists = useCallback(async (preferredId = selectedId) => {
    setLoading(true);
    setError("");
    try {
      const payload = await wishlistApi.lists();
      let lists = payload?.results || [];
      if (!lists.length) {
        const defaultPayload = await wishlistApi.defaultList();
        if (defaultPayload?.wishlist) {
          lists = [defaultPayload.wishlist];
        }
      }
      setWishlists(lists);
      const nextSelected = preferredId || lists.find((list) => list.is_default)?.id || lists[0]?.id || "";
      setSelectedId(nextSelected ? String(nextSelected) : "");
      if (nextSelected) {
        const detailPayload = await wishlistApi.list(nextSelected);
        setWishlist(detailPayload?.wishlist || null);
      } else {
        setWishlist(null);
      }
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load wishlists.").message);
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  const loadWishlistDetail = useCallback(async (wishlistId) => {
    if (!wishlistId) return;
    setLoading(true);
    setError("");
    try {
      const payload = await wishlistApi.list(wishlistId);
      setWishlist(payload?.wishlist || null);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not load wishlist.").message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWishlists();
  }, [loadWishlists]);

  useEffect(() => {
    if (!wishlist) return;
    setEditingName(wishlist.name || "");
    setEditingVisibility(wishlist.visibility || "Private");
    setShareLink("");
  }, [wishlist]);

  async function handleSelect(wishlistId) {
    setSelectedId(String(wishlistId));
    await loadWishlistDetail(wishlistId);
  }

  async function handleCreate(event) {
    event.preventDefault();
    const name = newListName.trim();
    if (!name) return;
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.createList({ name, visibility: "Private" });
      setNewListName("");
      notify({ title: "Wishlist created", message: `${name} is ready.`, icon: "playlist_add" });
      await loadWishlists(payload?.wishlist?.id);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not create wishlist.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(event) {
    event.preventDefault();
    if (!wishlist?.id) return;
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.updateList(wishlist.id, {
        name: editingName,
        visibility: editingVisibility
      });
      setWishlist(payload?.wishlist || wishlist);
      notify({ title: "Wishlist saved", message: "Wishlist details were updated.", icon: "save" });
      await loadWishlists(wishlist.id);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not save wishlist.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!wishlist?.id || wishlist.is_default) return;
    setSaving(true);
    setError("");
    try {
      await wishlistApi.deleteList(wishlist.id);
      notify({ title: "Wishlist deleted", message: "The wishlist was removed.", icon: "delete" });
      await loadWishlists("");
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not delete wishlist.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleShare(regenerate = false) {
    if (!wishlist?.id) return;
    setSaving(true);
    setError("");
    let payload = null;
    try {
      payload = await wishlistApi.share(wishlist.id, {
        visibility: editingVisibility === "Public" ? "Public" : "Shared",
        regenerate
      });
      setWishlist(payload?.wishlist || wishlist);
      notify({ title: "Share link ready", message: "Wishlist link copied if your browser allowed it.", icon: "ios_share" });
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not share wishlist.").message);
      setSaving(false);
      return;
    }
    if (!payload?.share_path) {
      setSaving(false);
      return;
    }
    const nextLink = `${window.location.origin}${payload.share_path.replace(/^\/api\/v1/, "")}`;
    setShareLink(nextLink);
    try {
      await navigator.clipboard.writeText(nextLink);
    } catch {
      // Clipboard may be blocked outside secure contexts; the link stays visible.
    }
    setSaving(false);
  }

  async function handleRemove(productId) {
    if (!wishlist?.id || !productId) return;
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.removeItem(wishlist.id, productId);
      setWishlist(payload?.wishlist || wishlist);
      if (wishlist.is_default) setStatus(productId, false);
      notify({ title: "Removed", message: "Product removed from this wishlist.", icon: "heart_minus" });
      await loadWishlists(wishlist.id);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not remove product.").message);
    } finally {
      setSaving(false);
    }
  }

  async function handleMove(productId, targetWishlistId) {
    if (!wishlist?.id || !productId || !targetWishlistId) return;
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.moveItem(wishlist.id, productId, { target_wishlist_id: Number(targetWishlistId) });
      setWishlist(payload?.source || wishlist);
      notify({ title: "Moved", message: "Product moved to another wishlist.", icon: "drive_file_move" });
      await loadWishlists(wishlist.id);
    } catch (requestError) {
      setError(normalizeApiError(requestError, "Could not move product.").message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="account-page wishlist-manager-page">
      <Link className="back-link" to="/account">
        <MaterialIcon name="arrow_back" size={18} /> Account
      </Link>

      <div className="wishlist-manager-hero">
        <div>
          <p className="eyebrow">Wishlists</p>
          <h1>Saved product lists</h1>
          <p>Create lists for projects, teams, quotations, or future purchases.</p>
        </div>
        <form className="wishlist-create-form" onSubmit={handleCreate}>
          <input value={newListName} placeholder="New wishlist name" onChange={(event) => setNewListName(event.target.value)} />
          <button className="primary-button" type="submit" disabled={saving || !newListName.trim()}>
            <MaterialIcon name="add" size={18} />
            Create
          </button>
        </form>
      </div>

      <Alert tone="warning">{error}</Alert>
      {loading ? <Spinner label="Loading wishlists" /> : null}

      {!loading && !wishlists.length ? (
        <EmptyState title="No wishlists yet" message="Create a wishlist or save a product to start one." />
      ) : null}

      {wishlists.length ? (
        <div className="wishlist-manager-layout">
          <aside className="wishlist-list-panel">
            {wishlists.map((list) => (
              <button
                className={`wishlist-list-button${String(list.id) === String(selectedId) ? " active" : ""}`}
                type="button"
                key={list.id}
                onClick={() => void handleSelect(list.id)}
              >
                <span>
                  <strong>{list.name}</strong>
                  <small>{list.line_count || 0} item{list.line_count === 1 ? "" : "s"} · {list.visibility}</small>
                </span>
                {list.is_default ? <em>Default</em> : null}
              </button>
            ))}
          </aside>

          <div className="wishlist-detail-panel">
            {wishlist?.id ? (
              <>
                <form className="wishlist-settings-panel" onSubmit={handleUpdate}>
                  <div>
                    <h2>{wishlist.name}</h2>
                    <p>{wishlist.line_count || items.length} saved item{items.length === 1 ? "" : "s"}</p>
                  </div>
                  <label>
                    <span>Name</span>
                    <input value={editingName} onChange={(event) => setEditingName(event.target.value)} />
                  </label>
                  <label>
                    <span>Visibility</span>
                    <select value={editingVisibility} onChange={(event) => setEditingVisibility(event.target.value)}>
                      <option value="Private">Private</option>
                      <option value="Shared">Shared</option>
                      <option value="Public">Public</option>
                    </select>
                  </label>
                  <div className="wishlist-settings-actions">
                    <button className="secondary-button" type="submit" disabled={saving || !editingName.trim()}>
                      <MaterialIcon name="save" size={18} />
                      Save
                    </button>
                    {!wishlist.is_default ? (
                      <button className="danger-link" type="button" disabled={saving} onClick={() => void handleDelete()}>
                        <MaterialIcon name="delete" size={18} />
                        Delete list
                      </button>
                    ) : null}
                  </div>
                </form>

                <div className="wishlist-share-panel surface-panel">
                  <div>
                    <strong>Share wishlist</strong>
                    <span>Create a link that opens this saved list.</span>
                  </div>
                  <button className="secondary-button" type="button" disabled={saving} onClick={() => void handleShare(false)}>
                    <MaterialIcon name="ios_share" size={18} />
                    Share
                  </button>
                  {shareLink ? (
                    <>
                      <input value={shareLink} readOnly aria-label="Wishlist share link" />
                      <button className="secondary-button" type="button" disabled={saving} onClick={() => void handleShare(true)}>
                        <MaterialIcon name="refresh" size={18} />
                        Regenerate
                      </button>
                    </>
                  ) : null}
                </div>

                {items.length ? (
                  <div className="wishlist-grid wishlist-manager-grid">
                    {items.map((item) => (
                      <WishlistManagerItem
                        key={item.id || item.product_id}
                        item={item}
                        saving={saving}
                        moveTargets={moveTargets}
                        onMove={handleMove}
                        onRemove={handleRemove}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <strong>No saved products</strong>
                    <p>Tap the save icon on products you want to compare later.</p>
                    <Link className="primary-button empty-state__action" to="/catalog">
                      <MaterialIcon name="storefront" size={18} />
                      Browse products
                    </Link>
                  </div>
                )}
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function WishlistManagerItem({ item, saving, moveTargets, onMove, onRemove }) {
  const productId = item.product_id || item.product?.id;
  const [targetId, setTargetId] = useState("");

  return (
    <div className="wishlist-manager-item">
      <WishlistCard item={item} saving={saving} onRemove={onRemove} />
      {moveTargets.length ? (
        <div className="wishlist-move-row">
          <select value={targetId} disabled={saving} onChange={(event) => setTargetId(event.target.value)}>
            <option value="">Move to...</option>
            {moveTargets.map((list) => (
              <option value={list.id} key={list.id}>{list.name}</option>
            ))}
          </select>
          <button className="secondary-button" type="button" disabled={saving || !targetId} onClick={() => void onMove(productId, targetId)}>
            <MaterialIcon name="drive_file_move" size={17} />
            Move
          </button>
        </div>
      ) : null}
    </div>
  );
}
