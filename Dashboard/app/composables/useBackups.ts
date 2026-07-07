export interface BackupRun {
  id: number
  backup_type: 'full' | 'database' | 'media'
  status: 'pending' | 'running' | 'success' | 'failed'
  storage_backend: string
  storage_path: string
  manifest_path: string
  checksum: string
  size_bytes: number
  size_mb: number
  app_version: string
  database_alias: string
  message: string
  metadata: Record<string, any>
  triggered_by: string
  started_at: string | null
  finished_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface BackupStatus {
  latest: BackupRun | null
  latest_success: BackupRun | null
  latest_failed: BackupRun | null
  success_count: number
  failed_count: number
  running_count: number
  storage_backend: string
  backup_root: string
}

export function useBackups() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const { apiBase, request } = useBackendApi()

  function parseError(err: any) {
    return err?.data?.error?.detail || err?.data?.detail || err?.message || 'Unknown error'
  }

  async function getBackups(params: { page?: number; pageSize?: number; status?: string; backupType?: string } = {}) {
    loading.value = true
    error.value = null
    const query = new URLSearchParams()
    if (params.page)
      query.set('page', String(params.page))
    if (params.pageSize)
      query.set('page_size', String(params.pageSize))
    if (params.status)
      query.set('status', params.status)
    if (params.backupType)
      query.set('backup_type', params.backupType)

    try {
      const suffix = query.toString() ? `?${query}` : ''
      const result = await request<{
        status: BackupStatus
        results: BackupRun[]
        pagination: { page: number; page_size: number; total: number; num_pages: number; has_next: boolean }
      }>(`/admin/backups/${suffix}`, { method: 'GET' })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = parseError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function createBackup(backupType: BackupRun['backup_type']) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ backup: BackupRun }>('/admin/backups/', {
        method: 'POST',
        body: { backup_type: backupType },
      })
      return { success: true, data: result.backup }
    }
    catch (err: any) {
      error.value = parseError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  async function verifyBackup(id: number) {
    loading.value = true
    error.value = null
    try {
      const result = await request<{ valid: boolean; expected_checksum: string; actual_checksum: string; size_bytes: number }>(`/admin/backups/${id}/verify/`, {
        method: 'POST',
      })
      return { success: true, data: result }
    }
    catch (err: any) {
      error.value = parseError(err)
      return { success: false, error: error.value }
    }
    finally {
      loading.value = false
    }
  }

  function downloadUrl(id: number) {
    return `${apiBase}/admin/backups/${id}/download/`
  }

  return {
    loading,
    error,
    getBackups,
    createBackup,
    verifyBackup,
    downloadUrl,
  }
}
