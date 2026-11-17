import { useState } from 'react'
import { searchMedicines } from '../../api/medicineApi'
import { useAsync } from '../../hooks/useAsync'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Badge from '../../components/Badge'
import DataTable from '../../components/DataTable'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function Medicines() {
  const [q, setQ] = useState('')
  const { data, loading, error, reload } = useAsync(() => searchMedicines(q), [q])
  const rows = data?.medicines || []

  const columns = [
    { key: 'medicine_name', header: 'Medicine', render: (r) => <strong>{r.medicine_name}</strong> },
    { key: 'strength', header: 'Strength' },
    { key: 'category', header: 'Category' },
    {
      key: 'prescription_required', header: 'Type',
      render: (r) => r.prescription_required ? <Badge tone="amber" dot>Prescription</Badge> : <Badge tone="green">OTC</Badge>,
    },
    {
      key: 'available_quantity', header: 'Available', align: 'right',
      render: (r) => <Badge tone={r.available_quantity > 0 ? 'green' : 'red'}>{r.available_quantity} units</Badge>,
    },
  ]

  return (
    <div>
      <PageHeader title="Medicines" subtitle="Search the catalogue and check availability" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}>
            <div className={shared.grow}>
              <Input
                type="search"
                placeholder="Search by name or category…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                leftIcon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>}
              />
            </div>
          </div>
        </Card>
        <Card padded={false}>
          <DataTable
            columns={columns}
            rows={rows}
            loading={loading}
            error={error}
            onRetry={reload}
            rowKey="medicine_id"
            emptyTitle="No medicines found"
            emptyMessage="Try a different search term, or leave the search blank to list all active medicines."
          />
        </Card>
      </Stack>
    </div>
  )
}
