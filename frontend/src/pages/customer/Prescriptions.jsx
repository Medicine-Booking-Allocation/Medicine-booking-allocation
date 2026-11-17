import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { submitPrescription, getUserPrescriptions } from '../../api/prescriptionApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Field from '../../components/Field'
import Input from '../../components/Input'
import Button from '../../components/Button'
import Stack from '../../components/Stack'
import StatusBadge from '../../components/StatusBadge'
import DataTable from '../../components/DataTable'
import shared from '../../styles/shared.module.css'

export default function Prescriptions() {
  const { user } = useAuth()
  const toast = useToast()
  const [form, setForm] = useState({ prescription_reference: '', prescribed_medicine: '', prescribed_dosage: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [reloadTick, setReloadTick] = useState(0)
  const { data, loading, error, reload } = useAsync(() => getUserPrescriptions(user?.user_id), [user?.user_id, reloadTick])

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const next = {}
    const ref = form.prescription_reference.trim()
    if (!ref) next.prescription_reference = 'Reference is required.'
    else if (ref.length > 150) next.prescription_reference = 'Cannot exceed 150 characters.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSubmitting(true)
    try {
      await submitPrescription({
        prescription_reference: ref,
        prescribed_medicine: form.prescribed_medicine.trim() || undefined,
        prescribed_dosage: form.prescribed_dosage.trim() || undefined,
      })
      toast.success('Prescription submitted for review.')
      setForm({ prescription_reference: '', prescribed_medicine: '', prescribed_dosage: '' })
      setReloadTick((t) => t + 1)
    } catch (err) {
      setErrors({ form: err?.response?.data?.error || 'Could not submit prescription.' })
    } finally {
      setSubmitting(false)
    }
  }

  const copy = (text) => {
    if (navigator.clipboard) navigator.clipboard.writeText(text)
    toast.info('Prescription ID copied.')
  }

  const rows = data?.prescriptions || []
  const columns = [
    { key: 'prescription_reference', header: 'Reference', render: (r) => <span className={shared.strong}>{r.prescription_reference}</span> },
    { key: 'prescribed_medicine', header: 'Medicine' },
    { key: 'prescribed_dosage', header: 'Dosage' },
    { key: 'prescription_status', header: 'Status', render: (r) => <StatusBadge status={r.prescription_status} /> },
    { key: 'submitted_at', header: 'Submitted', render: (r) => formatDateTime(r.submitted_at) },
    { key: 'verified_at', header: 'Verified', render: (r) => formatDateTime(r.verified_at) },
    { key: 'prescription_id', header: 'ID', render: (r) => <Button variant="ghost" size="sm" onClick={() => copy(r.prescription_id)}>Copy ID</Button> },
  ]

  return (
    <div>
      <PageHeader title="Prescriptions" subtitle="Submit prescription reference details for verification" />
      <Stack gap="5">
        <Card title="Submit prescription reference details">
          <form onSubmit={handleSubmit} noValidate>
            <Stack gap="4">
              {errors.form && <div className={`${shared.note} ${shared.noteDanger}`}>{errors.form}</div>}
              <Field label="Prescription reference" required error={errors.prescription_reference} hint="Enter the reference details — the backend does not support file uploads.">
                <Input value={form.prescription_reference} onChange={(e) => set('prescription_reference', e.target.value)} invalid={!!errors.prescription_reference} placeholder="e.g. RX-2026-0001 / Dr. Sharma" />
              </Field>
              <div className={shared.formGrid}>
                <Field label="Prescribed medicine" hint="Optional">
                  <Input value={form.prescribed_medicine} onChange={(e) => set('prescribed_medicine', e.target.value)} placeholder="e.g. Amoxicillin" />
                </Field>
                <Field label="Prescribed dosage" hint="Optional">
                  <Input value={form.prescribed_dosage} onChange={(e) => set('prescribed_dosage', e.target.value)} placeholder="e.g. 500mg twice daily" />
                </Field>
              </div>
              <Button type="submit" loading={submitting}>Submit for review</Button>
            </Stack>
          </form>
        </Card>

        <Card title="My prescriptions" padded={false}>
          <DataTable
            columns={columns}
            rows={rows}
            loading={loading}
            error={error}
            onRetry={reload}
            rowKey="prescription_id"
            emptyTitle="No prescriptions yet"
            emptyMessage="Submitted prescriptions will appear here."
          />
        </Card>
      </Stack>
    </div>
  )
}
