import { useState } from 'react'
import { getPrescription, updatePrescriptionStatus } from '../../api/prescriptionApi'
import { useToast } from '../../components/ToastContext'
import { PRESCRIPTION_TRANSITIONS, formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import DetailList from '../../components/DetailList'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function PrescriptionReview() {
  const toast = useToast()
  const [id, setId] = useState('')
  const [rx, setRx] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lookupError, setLookupError] = useState('')
  const [busy, setBusy] = useState('')

  const lookup = async (e) => {
    e?.preventDefault()
    if (!id.trim()) return
    setLoading(true); setLookupError(''); setRx(null)
    try { setRx(await getPrescription(id.trim())) }
    catch (err) { setLookupError(err?.response?.data?.error || 'Prescription not found.') }
    finally { setLoading(false) }
  }

  const apply = async (newStatus) => {
    setBusy(newStatus)
    try {
      const data = await updatePrescriptionStatus(rx.prescription_id, newStatus)
      toast.success(`Status updated to ${data.prescription_status}.`)
      setRx(await getPrescription(rx.prescription_id))
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Could not update status.')
    } finally { setBusy('') }
  }

  const transitions = rx ? (PRESCRIPTION_TRANSITIONS[rx.prescription_status] || []) : []

  return (
    <div>
      <PageHeader title="Prescriptions" subtitle="Verify or reject a prescription by ID" />
      <Stack gap="4">
        <Card title="Lookup by Prescription ID">
          <form onSubmit={lookup} className={shared.inline}>
            <div className={shared.grow}><Input placeholder="Enter prescription ID…" value={id} onChange={(e) => setId(e.target.value)} /></div>
            <Button type="submit" loading={loading}>Lookup</Button>
          </form>
          <p className={shared.meta} style={{ marginTop: 8 }}>Customers can copy their prescription ID from their Prescriptions tab to share with you.</p>
          {lookupError && <div className={`${shared.note} ${shared.noteDanger}`} style={{ marginTop: 12 }}>{lookupError}</div>}
        </Card>
        {rx && (
          <Card title="Prescription" actions={<StatusBadge status={rx.prescription_status} />}>
            <Stack gap="3">
              <DetailList items={[
                { label: 'Prescription ID', value: <span className={shared.codeBox}>{rx.prescription_id}</span> },
                { label: 'User ID', value: <span className={shared.codeBox}>{rx.user_id}</span> },
                { label: 'Reference', value: rx.prescription_reference },
                { label: 'Prescribed medicine', value: rx.prescribed_medicine || '—' },
                { label: 'Prescribed dosage', value: rx.prescribed_dosage || '—' },
                { label: 'Submitted', value: formatDateTime(rx.submitted_at) },
                { label: 'Verified', value: formatDateTime(rx.verified_at) },
              ]} />
              <div className={shared.inline}>
                {transitions.map((t) => (
                  <Button key={t} variant={t === 'Rejected' ? 'danger' : t === 'Verified' ? 'success' : 'secondary'} loading={busy === t} onClick={() => apply(t)}>
                    Mark as {t}
                  </Button>
                ))}
                {transitions.length === 0 && <span className={shared.meta}>No further status transitions available.</span>}
              </div>
            </Stack>
          </Card>
        )}
      </Stack>
    </div>
  )
}
