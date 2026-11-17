import { useState } from 'react'
import { getPriorityRules, createPriorityRule, updatePriorityRule } from '../../api/adminApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Field from '../../components/Field'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import DataTable from '../../components/DataTable'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function PriorityRules() {
  const toast = useToast()
  const [statusFilter, setStatusFilter] = useState('')
  const { data, loading, error, reload } = useAsync(() => getPriorityRules({ status: statusFilter || undefined }), [statusFilter])
  const [form, setForm] = useState({ rule_name: '', version: '', urgency_weight: '', availability_weight: '', patient_history_weight: '', status: 'Active' })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))
  const num = (v) => { const n = parseFloat(v); return Number.isFinite(n) ? n : null }

  const submit = async (e) => {
    e.preventDefault()
    const u = num(form.urgency_weight), a = num(form.availability_weight), p = num(form.patient_history_weight)
    const next = {}
    if (!form.rule_name.trim()) next.rule_name = 'Required.'
    if (!form.version.trim()) next.version = 'Required.'
    if (u == null || a == null || p == null) next.weights = 'All three weights are required.'
    else if (Math.abs((u + a + p) - 1) > 1e-6) next.weights = 'Weights must sum to 1.0.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSaving(true)
    try {
      await createPriorityRule({ rule_name: form.rule_name.trim(), version: form.version.trim(), status: form.status, urgency_weight: u, availability_weight: a, patient_history_weight: p })
      toast.success('Priority rule created.')
      setForm({ rule_name: '', version: '', urgency_weight: '', availability_weight: '', patient_history_weight: '', status: 'Active' })
      reload()
    } catch (err) { setErrors({ form: err?.response?.data?.error || 'Could not create rule.' }) }
    finally { setSaving(false) }
  }

  const toggleStatus = async (r) => {
    try { await updatePriorityRule(r.rule_id, { status: r.status === 'Active' ? 'Inactive' : 'Active' }); toast.success('Rule status updated.'); reload() }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not update.') }
  }

  const rows = data?.priority_rules || []
  const columns = [
    { key: 'rule_name', header: 'Name', render: (r) => <strong>{r.rule_name}</strong> },
    { key: 'version', header: 'Version', render: (r) => <span className={shared.codeBox}>{r.version}</span> },
    { key: 'urgency_weight', header: 'Urgency', align: 'right' },
    { key: 'availability_weight', header: 'Availability', align: 'right' },
    { key: 'patient_history_weight', header: 'History', align: 'right' },
    { key: 'status', header: 'Status', render: (r) => <Badge tone={r.status === 'Active' ? 'green' : 'neutral'} dot>{r.status}</Badge> },
    { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
    { key: 'actions', header: '', align: 'right', render: (r) => <Button size="sm" variant="ghost" onClick={() => toggleStatus(r)}>{r.status === 'Active' ? 'Deactivate' : 'Activate'}</Button> },
  ]

  return (
    <div>
      <PageHeader title="Priority rules" subtitle="Weight urgency, availability and patient history" />
      <Stack gap="5">
        <Card title="Create priority rule">
          <form onSubmit={submit} noValidate>
            <Stack gap="4">
              {errors.form && <div className={`${shared.note} ${shared.noteDanger}`}>{errors.form}</div>}
              <div className={shared.formGrid}>
                <Field label="Rule name" required error={errors.rule_name}><Input value={form.rule_name} onChange={(e) => set('rule_name', e.target.value)} invalid={!!errors.rule_name} placeholder="e.g. Urgency-led" /></Field>
                <Field label="Version" required error={errors.version}><Input value={form.version} onChange={(e) => set('version', e.target.value)} invalid={!!errors.version} placeholder="e.g. v2.0" /></Field>
              </div>
              <div className={shared.formGrid}>
                <Field label="Urgency weight" hint="0–1"><Input type="number" step="0.01" min="0" max="1" value={form.urgency_weight} onChange={(e) => set('urgency_weight', e.target.value)} /></Field>
                <Field label="Availability weight" hint="0–1"><Input type="number" step="0.01" min="0" max="1" value={form.availability_weight} onChange={(e) => set('availability_weight', e.target.value)} /></Field>
                <Field label="Patient history weight" hint="0–1"><Input type="number" step="0.01" min="0" max="1" value={form.patient_history_weight} onChange={(e) => set('patient_history_weight', e.target.value)} /></Field>
                <Field label="Status"><Select value={form.status} onChange={(e) => set('status', e.target.value)}><option value="Active">Active</option><option value="Inactive">Inactive</option></Select></Field>
              </div>
              {errors.weights && <div className={`${shared.note} ${shared.noteDanger}`}>{errors.weights}</div>}
              <Button type="submit" loading={saving}>Create rule</Button>
            </Stack>
          </form>
        </Card>
        <Card title="Existing rules" actions={
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All</option><option value="Active">Active</option><option value="Inactive">Inactive</option>
          </Select>
        } padded={false}>
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey="rule_id" emptyTitle="No rules" emptyMessage="No priority rules match." />
        </Card>
      </Stack>
    </div>
  )
}
