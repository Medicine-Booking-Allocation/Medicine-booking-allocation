import { useState } from 'react'
import { getUsers, updateUserRole } from '../../api/adminApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { ROLES_LIST, formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Select from '../../components/Select'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import StatusBadge from '../../components/StatusBadge'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function Users() {
  const toast = useToast()
  const [role, setRole] = useState('')
  const [account_status, setAccountStatus] = useState('')
  const { data, loading, error, reload } = useAsync(
    () => getUsers({ role: role || undefined, account_status: account_status || undefined }),
    [role, account_status]
  )
  const [editUser, setEditUser] = useState(null)
  const [newRole, setNewRole] = useState('')
  const [saving, setSaving] = useState(false)
  const rows = data?.users || []

  const save = async () => {
    setSaving(true)
    try {
      const res = await updateUserRole(editUser.user_id, newRole)
      toast.success(`Role changed to ${res.new_role}.`)
      setEditUser(null)
      reload()
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Could not update role.')
    } finally { setSaving(false) }
  }

  const columns = [
    { key: 'full_name', header: 'Name', render: (r) => <strong>{r.full_name}</strong> },
    { key: 'email', header: 'Email' },
    { key: 'phone', header: 'Phone' },
    { key: 'role', header: 'Role', render: (r) => <Badge tone="navy">{r.role}</Badge> },
    { key: 'account_status', header: 'Status', render: (r) => <StatusBadge status={r.account_status} /> },
    { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
    { key: 'actions', header: '', align: 'right', render: (r) => <Button size="sm" variant="secondary" onClick={() => { setEditUser(r); setNewRole(r.role) }}>Change role</Button> },
  ]

  return (
    <div>
      <PageHeader title="Users" subtitle="Manage user roles" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}>
            <div className={shared.grow}>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="">All roles</option>
                {ROLES_LIST.map((r) => <option key={r} value={r}>{r}</option>)}
              </Select>
            </div>
            <div className={shared.grow}>
              <Select value={account_status} onChange={(e) => setAccountStatus(e.target.value)}>
                <option value="">All statuses</option>
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </Select>
            </div>
          </div>
        </Card>
        <Card padded={false}>
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey="user_id" emptyTitle="No users" emptyMessage="No users match these filters." />
        </Card>
        <div className={`${shared.note} ${shared.noteInfo}`}>Account activation/deactivation is not supported by the backend — only role changes are available here.</div>
      </Stack>
      <Modal
        open={!!editUser}
        onClose={() => setEditUser(null)}
        title="Change user role"
        size="sm"
        footer={<><Button variant="ghost" onClick={() => setEditUser(null)}>Cancel</Button><Button onClick={save} loading={saving}>Save</Button></>}
      >
        {editUser && (
          <Stack gap="3">
            <p className={shared.meta}>{editUser.full_name} · {editUser.email}</p>
            <p className={shared.meta}>Current role: <Badge tone="navy">{editUser.role}</Badge></p>
            <Select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
              {ROLES_LIST.map((r) => <option key={r} value={r}>{r}</option>)}
            </Select>
          </Stack>
        )}
      </Modal>
    </div>
  )
}
