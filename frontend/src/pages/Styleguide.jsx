import { useEffect, useState } from 'react'
import client from '../api/client'
import { useToast } from '../components/ToastContext'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import Field from '../components/Field'
import Input from '../components/Input'
import Textarea from '../components/Textarea'
import Select from '../components/Select'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import Container from '../components/Container'
import Stack from '../components/Stack'
import Row from '../components/Row'
import Grid from '../components/Grid'
import styles from './Styleguide.module.css'

/*
 * Temporary design-system showcase. Renders every shared primitive so the
 * UI library can be reviewed in the browser. Task 4 replaces this screen with
 * real routing and the three role portals. The header also calls the real
 * /health endpoint to confirm the Flask proxy still works end to end.
 */

const SWATCHES = [
  ['Navy', 'var(--p47-navy)'],
  ['Navy 700', 'var(--p47-navy-700)'],
  ['Teal', 'var(--p47-teal)'],
  ['Teal 600', 'var(--p47-teal-600)'],
  ['Green', 'var(--p47-green)'],
  ['Green 600', 'var(--p47-green-600)'],
  ['White', 'var(--p47-white)'],
  ['Surface', 'var(--p47-surface)'],
]

const STATUSES = [
  'Requested', 'Allocated', 'Waitlisted', 'Fulfilled', 'Cancelled', 'Rejected',
  'Submitted', 'Under Review', 'Verified', 'Active', 'Promoted',
  'Pending', 'Sent', 'Delivered', 'Inactive',
]

function Section({ title, children }) {
  return (
    <Card title={title} className={styles.section}>
      <Stack gap="5">{children}</Stack>
    </Card>
  )
}

export default function Styleguide() {
  const toast = useToast()
  const [health, setHealth] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    let active = true
    client
      .get('/health')
      .then((r) => { if (active) setHealth(r.data) })
      .catch(() => { if (active) setHealth(null) })
    return () => { active = false }
  }, [])

  const handleConfirm = () => {
    setConfirming(true)
    setTimeout(() => {
      setConfirming(false)
      setConfirmOpen(false)
      toast.success('Action confirmed.')
    }, 700)
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Container>
          <Row justify="between" wrap>
            <Stack gap="1">
              <h1 className={styles.title}>Project 47 — Design System</h1>
              <p className={styles.lead}>Priority-Based Medicine Booking &amp; Allocation · shared UI library</p>
            </Stack>
            <div className={styles.health}>
              <span className={styles.healthLabel}>Backend</span>
              {health ? <StatusBadge status="Active" dot /> : <Badge tone="amber" dot>checking…</Badge>}
              <span className={styles.healthText}>{health ? health.project : 'unreachable'}</span>
            </div>
          </Row>
        </Container>
      </header>

      <main className={styles.main}>
        <Container>
          <Stack gap="6">
            <Section title="Typography">
              <h1 className={styles.h1}>Heading level 1</h1>
              <h2 className={styles.h2}>Heading level 2</h2>
              <h3 className={styles.h3}>Heading level 3</h3>
              <p className={styles.body}>Body text — used for paragraphs and content throughout the portals.</p>
              <p className={styles.muted}>Muted helper text for secondary information.</p>
            </Section>

            <Section title="Color palette">
              <Grid min="120px" gap="4">
                {SWATCHES.map(([name, color]) => (
                  <div key={name} className={styles.swatch}>
                    <div className={styles.swatchFill} style={{ background: color }} />
                    <span className={styles.swatchName}>{name}</span>
                  </div>
                ))}
              </Grid>
            </Section>

            <Section title="Buttons">
              <Row gap="3" wrap>
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="success">Success</Button>
                <Button variant="danger">Danger</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="subtle">Subtle</Button>
              </Row>
              <Row gap="3" wrap>
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
                <Button loading>Loading</Button>
                <Button disabled>Disabled</Button>
              </Row>
            </Section>

            <Section title="Badges & status">
              <Row gap="2" wrap>
                {['navy', 'teal', 'green', 'amber', 'red', 'blue', 'neutral'].map((t) => (
                  <Badge key={t} tone={t} dot>{t}</Badge>
                ))}
              </Row>
              <Row gap="2" wrap>
                {STATUSES.map((s) => <StatusBadge key={s} status={s} />)}
              </Row>
            </Section>

            <Section title="Form controls">
              <div className={styles.formGrid}>
                <Field label="Email" required hint="We never share your email.">
                  <Input type="email" placeholder="you@example.com" />
                </Field>
                <Field label="Urgency" required>
                  <Select defaultValue="">
                    <option value="" disabled>Select urgency…</option>
                    <option value="emergency">Emergency</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </Select>
                </Field>
                <Field label="Quantity" error="Quantity must be a positive integer.">
                  <Input type="number" defaultValue="0" invalid />
                </Field>
                <div style={{ gridColumn: '1 / -1' }}>
                  <Field label="Prescription reference" hint="Enter reference details, not a file upload.">
                    <Textarea rows={3} placeholder="e.g. RX-2026-0001 — Dr. …" />
                  </Field>
                </div>
              </div>
            </Section>

            <Section title="Feedback">
              <Row gap="4" wrap>
                <Row gap="2">
                  <Spinner tone="navy" />
                  <Spinner tone="teal" />
                  <Spinner size="lg" tone="teal" />
                </Row>
                <Row gap="2">
                  <Button variant="subtle" onClick={() => toast.success('Saved successfully.')}>Success toast</Button>
                  <Button variant="ghost" onClick={() => toast.error('Something went wrong.')}>Error toast</Button>
                  <Button variant="ghost" onClick={() => toast.info('For your information.')}>Info toast</Button>
                  <Button variant="ghost" onClick={() => toast.warning('Please review the entry.')}>Warning toast</Button>
                </Row>
              </Row>
            </Section>

            <Section title="Overlays">
              <Row gap="3">
                <Button onClick={() => setModalOpen(true)}>Open modal</Button>
                <Button variant="danger" onClick={() => setConfirmOpen(true)}>Open confirm</Button>
              </Row>
            </Section>

            <Section title="States">
              <Grid min="260px" gap="4">
                <EmptyState
                  title="No bookings yet"
                  message="When you create a booking it will appear here."
                  action={<Button variant="subtle" size="sm">New booking</Button>}
                />
                <ErrorState
                  title="Could not load"
                  message="The server didn't respond in time."
                  action={<Button variant="ghost" size="sm" onClick={() => toast.info('Retrying…')}>Try again</Button>}
                />
              </Grid>
            </Section>

            <Section title="Layout">
              <Grid min="200px" gap="4">
                {[1, 2, 3].map((i) => (
                  <Card key={i} subtitle={`Card ${i}`} elevation="sm">
                    Responsive grid item — collapses on small screens.
                  </Card>
                ))}
              </Grid>
            </Section>
          </Stack>
        </Container>
      </main>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Demo modal"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>Close</Button>
            <Button onClick={() => { setModalOpen(false); toast.success('Done.') }}>Confirm</Button>
          </>
        }
      >
        <p className={styles.modalBody}>
          This modal demonstrates overlay, Esc-to-close and body-scroll lock. It is built on the shared{' '}
          <code>&lt;Modal&gt;</code> primitive.
        </p>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirm}
        loading={confirming}
        tone="danger"
        title="Cancel booking?"
        message="This releases the reserved stock and cannot be undone."
        confirmLabel="Yes, cancel"
        cancelLabel="Keep"
      />
    </div>
  )
}
