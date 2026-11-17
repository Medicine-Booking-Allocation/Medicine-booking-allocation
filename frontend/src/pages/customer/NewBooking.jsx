import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { searchMedicines } from '../../api/medicineApi'
import { getUserPrescriptions } from '../../api/prescriptionApi'
import { createBooking } from '../../api/bookingApi'
import { addBooking } from '../../utils/bookingStore'
import { useToast } from '../../components/ToastContext'
import { URGENCY_OPTIONS } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Field from '../../components/Field'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Button from '../../components/Button'
import Stack from '../../components/Stack'
import StatusBadge from '../../components/StatusBadge'
import DetailList from '../../components/DetailList'
import shared from '../../styles/shared.module.css'

export default function NewBooking() {
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [meds, setMeds] = useState([])
  const [medsLoading, setMedsLoading] = useState(true)
  const [rxs, setRxs] = useState([])
  const [form, setForm] = useState({ medicine_id: '', quantity: '1', urgency: '', prescription_id: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    searchMedicines('').then((d) => setMeds(d.medicines || [])).finally(() => setMedsLoading(false))
  }, [])
  useEffect(() => {
    if (user) getUserPrescriptions(user.user_id).then((d) => setRxs(d.prescriptions || [])).catch(() => {})
  }, [user])

  const selectedMed = meds.find((m) => m.medicine_id === form.medicine_id)
  const needsRx = !!selectedMed?.prescription_required
  const eligibleRx = rxs.filter((p) => p.prescription_status !== 'Rejected')

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const next = {}
    if (!form.medicine_id) next.medicine_id = 'Select a medicine.'
    const qty = parseInt(form.quantity, 10)
    if (!Number.isInteger(qty) || qty <= 0) next.quantity = 'Enter a positive integer.'
    if (!form.urgency) next.urgency = 'Select an urgency level.'
    if (needsRx && !form.prescription_id) next.prescription_id = 'A prescription is required for this medicine.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSubmitting(true)
    setResult(null)
    try {
      const data = await createBooking({
        medicine_id: form.medicine_id,
        quantity: qty,
        urgency: form.urgency,
        prescription_id: needsRx ? form.prescription_id : undefined,
      })
      addBooking(user.user_id, data.booking_id, data.waitlist_position ?? null)
      setResult({ ...data, quantity: qty, medicine_name: selectedMed?.medicine_name })
      toast.success('Booking created.')
    } catch (err) {
      setErrors({ form: err?.response?.data?.error || 'Could not create booking.' })
    } finally {
      setSubmitting(false)
    }
  }

  const resultTone = result?.status === 'Allocated' ? shared.resultOk : result?.status === 'Waitlisted' ? shared.resultWait : shared.resultInfo

  return (
    <div>
      <PageHeader title="New booking" subtitle="Request a medicine with a priority urgency" />
      <Stack gap="5">
        <Card title="Booking details">
          <form onSubmit={handleSubmit} noValidate>
            <Stack gap="4">
              {errors.form && <div className={`${shared.note} ${shared.noteDanger}`}>{errors.form}</div>}
              <Field label="Medicine" required error={errors.medicine_id}>
                <Select value={form.medicine_id} onChange={(e) => set('medicine_id', e.target.value)} invalid={!!errors.medicine_id}>
                  <option value="">{medsLoading ? 'Loading medicines…' : 'Select a medicine'}</option>
                  {meds.map((m) => (
                    <option key={m.medicine_id} value={m.medicine_id}>
                      {m.medicine_name}{m.strength ? ` · ${m.strength}` : ''}{m.prescription_required ? ' · Rx' : ''} ({m.available_quantity} avail.)
                    </option>
                  ))}
                </Select>
              </Field>
              {selectedMed && (
                <div className={`${shared.note} ${shared.noteInfo}`}>
                  {selectedMed.prescription_required ? 'This medicine requires a prescription.' : 'Over-the-counter — no prescription needed.'} Available: {selectedMed.available_quantity} units.
                </div>
              )}
              {needsRx && (
                <Field label="Prescription" required error={errors.prescription_id} hint={eligibleRx.length ? 'Verified prescriptions are processed first.' : 'You have no eligible prescriptions — submit one in the Prescriptions tab.'}>
                  <Select value={form.prescription_id} onChange={(e) => set('prescription_id', e.target.value)} invalid={!!errors.prescription_id}>
                    <option value="">Select a prescription</option>
                    {eligibleRx.map((p) => (
                      <option key={p.prescription_id} value={p.prescription_id}>{p.prescription_reference} ({p.prescription_status})</option>
                    ))}
                  </Select>
                </Field>
              )}
              <div className={shared.formGrid}>
                <Field label="Quantity" required error={errors.quantity} hint="Positive whole units.">
                  <Input type="number" min="1" value={form.quantity} onChange={(e) => set('quantity', e.target.value)} invalid={!!errors.quantity} />
                </Field>
                <Field label="Urgency" required error={errors.urgency}>
                  <Select value={form.urgency} onChange={(e) => set('urgency', e.target.value)} invalid={!!errors.urgency}>
                    <option value="">Select urgency…</option>
                    {URGENCY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </Select>
                </Field>
              </div>
              <Button type="submit" size="lg" loading={submitting}>Create booking</Button>
            </Stack>
          </form>
        </Card>

        {result && (
          <div className={`${shared.resultCard} ${resultTone}`}>
            <Stack gap="3">
              <div className={shared.inline}>
                <StatusBadge status={result.status} />
                {result.status === 'Waitlisted' && result.waitlist_position != null && <span className={shared.meta}>Position #{result.waitlist_position}</span>}
              </div>
              <h3 className={shared.strong}>Booking created</h3>
              <DetailList items={[
                { label: 'Booking ID', value: <span className={shared.codeBox}>{result.booking_id}</span> },
                { label: 'Priority score', value: result.priority_score },
                { label: 'Medicine', value: result.medicine_name },
                { label: 'Quantity', value: result.quantity },
              ]} />
              <p className={shared.meta}>
                {result.status === 'Allocated' && 'Stock allocated — pharmacy staff will fulfil it.'}
                {result.status === 'Waitlisted' && 'Insufficient stock — you are in the priority queue. Position may change as others are promoted.'}
                {result.status === 'Requested' && 'Awaiting prescription verification before allocation.'}
              </p>
              <div><Button variant="subtle" onClick={() => navigate('/customer/bookings')}>View my bookings</Button></div>
            </Stack>
          </div>
        )}
      </Stack>
    </div>
  )
}
