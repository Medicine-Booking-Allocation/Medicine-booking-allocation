import { useState } from 'react'
import { searchMedicines } from '../../api/medicineApi'
import { getInventory, addStock, reserveStock, releaseStock } from '../../api/inventoryApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import DataTable from '../../components/DataTable'
import DetailList from '../../components/DetailList'
import Spinner from '../../components/Spinner'
import Stack from '../../components/Stack'
import Row from '../../components/Row'
import shared from '../../styles/shared.module.css'

export default function Inventory() {
  const toast = useToast()
  const [q, setQ] = useState('')
  const { data, loading, error, reload } = useAsync(() => searchMedicines(q), [q])
  const [selectedId, setSelectedId] = useState(null)
  const meds = data?.medicines || []
  const selectedMed = meds.find((m) => m.medicine_id === selectedId)
  const inv = useAsync(() => (selectedId ? getInventory(selectedId) : Promise.resolve(null)), [selectedId])
  const [qty, setQty] = useState({ add: '', reserve: '', release: '' })
  const [busy, setBusy] = useState('')

  const run = async (action) => {
    const value = parseInt(qty[action], 10)
    if (!Number.isInteger(value) || value <= 0) { toast.error('Enter a positive integer.'); return }
    setBusy(action)
    try {
      let res
      if (action === 'add') res = await addStock({ medicine_id: selectedId, quantity: value })
      else if (action === 'reserve') res = await reserveStock({ medicine_id: selectedId, quantity: value })
      else res = await releaseStock({ medicine_id: selectedId, quantity: value })
      toast.success(res.message || 'Done.')
      if (action === 'add' && res.promoted_count != null) toast.info(`${res.promoted_count} waitlisted booking(s) auto-promoted.`)
      inv.reload()
      setQty((s) => ({ ...s, [action]: '' }))
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Operation failed.')
    } finally { setBusy('') }
  }

  const columns = [
    { key: 'medicine_name', header: 'Medicine', render: (r) => <strong>{r.medicine_name}</strong> },
    { key: 'strength', header: 'Strength' },
    { key: 'category', header: 'Category' },
    { key: 'prescription_required', header: 'Type', render: (r) => r.prescription_required ? <Badge tone="amber" dot>Rx</Badge> : <Badge tone="green">OTC</Badge> },
    { key: 'available_quantity', header: 'Available', align: 'right', render: (r) => <Badge tone={r.available_quantity > 0 ? 'green' : 'red'}>{r.available_quantity}</Badge> },
    { key: 'actions', header: '', align: 'right', render: (r) => <Button size="sm" variant={r.medicine_id === selectedId ? 'subtle' : 'secondary'} onClick={() => setSelectedId(r.medicine_id)}>Manage</Button> },
  ]

  return (
    <div>
      <PageHeader title="Inventory" subtitle="View stock and add / reserve / release quantities" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}><div className={shared.grow}><Input type="search" placeholder="Search medicines…" value={q} onChange={(e) => setQ(e.target.value)} /></div></div>
        </Card>
        <Card padded={false}>
          <DataTable columns={columns} rows={meds} loading={loading} error={error} onRetry={reload} rowKey="medicine_id" emptyTitle="No medicines" emptyMessage="No medicines match your search." />
        </Card>
        {selectedMed && (
          <Card title={`Inventory — ${selectedMed.medicine_name}`} subtitle={selectedMed.strength || ''}>
            <Stack gap="4">
              {inv.loading ? (
                <div className={shared.inline}><Spinner size="sm" /><span className={shared.meta}>Loading…</span></div>
              ) : inv.error ? (
                <div className={`${shared.note} ${shared.noteDanger}`}>{inv.error}</div>
              ) : inv.data ? (
                <DetailList items={[
                  { label: 'Available', value: inv.data.available_quantity },
                  { label: 'Reserved', value: inv.data.reserved_quantity },
                  { label: 'Fulfilled', value: inv.data.fulfilled_quantity },
                  { label: 'Last updated', value: formatDateTime(inv.data.last_updated_at) },
                ]} />
              ) : (
                <div className={shared.note}>No inventory record yet — add stock to create one.</div>
              )}
              <div className={shared.formGrid}>
                <div>
                  <p className={shared.meta}>Add stock (auto-promotes waitlist)</p>
                  <Row gap="2">
                    <Input type="number" min="1" placeholder="Qty" value={qty.add} onChange={(e) => setQty((s) => ({ ...s, add: e.target.value }))} />
                    <Button size="sm" loading={busy === 'add'} onClick={() => run('add')}>Add</Button>
                  </Row>
                </div>
                <div>
                  <p className={shared.meta}>Reserve stock</p>
                  <Row gap="2">
                    <Input type="number" min="1" placeholder="Qty" value={qty.reserve} onChange={(e) => setQty((s) => ({ ...s, reserve: e.target.value }))} />
                    <Button size="sm" variant="secondary" loading={busy === 'reserve'} onClick={() => run('reserve')}>Reserve</Button>
                  </Row>
                </div>
                <div>
                  <p className={shared.meta}>Release reserved → available</p>
                  <Row gap="2">
                    <Input type="number" min="1" placeholder="Qty" value={qty.release} onChange={(e) => setQty((s) => ({ ...s, release: e.target.value }))} />
                    <Button size="sm" variant="ghost" loading={busy === 'release'} onClick={() => run('release')}>Release</Button>
                  </Row>
                </div>
              </div>
            </Stack>
          </Card>
        )}
      </Stack>
    </div>
  )
}
