
import { useEffect, useState } from 'react'

// ========================================
// 1. Data Types
// ========================================

type WaferLot = {
  lot_id: string
  wafer_count: number
  route_id: string | null
  status: string
  current_step_index: number
}

type Equipment = {
  equipment_id: string
  process_step: string
  status: string
  current_lot_id: string | null
}

type Carrier = {
  carrier_id: string
  lot_id: string
  current_station: string
  status: string
}

type TransportJob = {
  job_id: string
  carrier_id: string
  origin_station: string
  destination_station: string
  status: string
  created_at: string
}

// ========================================
// 2. Reusable API Data Hook
// ========================================

function useApiList<T>(path: string) {
  const [items, setItems] = useState<T[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadData() {
      try {
        const response = await fetch(path, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data: T[] = await response.json()

        if (!Array.isArray(data)) {
          throw new Error('Unexpected API response')
        }

        setItems(data)
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load data'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadData()

    return () => controller.abort()
  }, [path])

  return { items, loading, error }
}

// ========================================
// 3. Status Badge Component
// ========================================

function StatusBadge({ status }: { status: string }) {
  const successStatuses = [
    'IDLE',
    'AVAILABLE',
    'DELIVERED',
    'COMPLETED',
  ]

  const activeStatuses = [
    'PROCESSING',
    'IN_PROGRESS',
    'IN_TRANSIT',
    'MOVING',
  ]

  let background = '#f1f5f9'
  let color = '#475569'

  if (successStatuses.includes(status)) {
    background = '#dcfce7'
    color = '#166534'
  } else if (activeStatuses.includes(status)) {
    background = '#dbeafe'
    color = '#1d4ed8'
  } else if (status === 'DOWN') {
    background = '#fee2e2'
    color = '#b91c1c'
  }

  return (
    <span
      style={{
        display: 'inline-block',
        background,
        color,
        padding: '7px 12px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 600,
        whiteSpace: 'nowrap',
      }}
    >
      {status}
    </span>
  )
}

// ========================================
// 4. Main SmartFab Application
// ========================================

function App() {
  // Load live data from FastAPI
  const {
    items: lots,
    loading: lotsLoading,
    error: lotsError,
  } = useApiList<WaferLot>('/api/lots')

  const {
    items: equipment,
    loading: equipmentLoading,
    error: equipmentError,
  } = useApiList<Equipment>('/api/equipment')

  const {
    items: carriers,
    loading: carriersLoading,
    error: carriersError,
  } = useApiList<Carrier>('/api/amhs/carriers')

  const {
    items: jobs,
    loading: jobsLoading,
    error: jobsError,
  } = useApiList<TransportJob>('/api/amhs/jobs')

  // ========================================
  // 5. Factory Overview Metrics
  // ========================================

  const metrics = [
    {
      label: 'Total Lots',
      value: lots.length,
    },
    {
      label: 'In Progress',
      value: lots.filter(
        (lot) => lot.status === 'IN_PROGRESS'
      ).length,
    },
    {
      label: 'Completed',
      value: lots.filter(
        (lot) => lot.status === 'COMPLETED'
      ).length,
    },
    {
      label: 'Total Wafers',
      value: lots.reduce(
        (total, lot) => total + lot.wafer_count,
        0
      ),
    },
  ]

  // ========================================
  // 6. Dashboard UI
  // ========================================

  return (
    <main>
      {/* Dashboard Header */}
      <header>
        <h1>SmartFab</h1>
        <p>
          Semiconductor Manufacturing Operations Dashboard
        </p>
      </header>

      {/* Factory Overview */}
      <section>
        <h2>Factory Overview</h2>

        {lotsLoading && <p>Loading factory metrics...</p>}

        {lotsError && (
          <p>Unable to load metrics: {lotsError}</p>
        )}

        {!lotsLoading && !lotsError && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
              gap: '14px',
            }}
          >
            {metrics.map((metric) => (
              <div
                key={metric.label}
                style={{
                  background: '#f3f6fb',
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '18px',
                }}
              >
                <p style={{ margin: '0 0 10px' }}>
                  {metric.label}
                </p>

                <strong
                  style={{
                    display: 'block',
                    fontSize: '30px',
                    color: '#17263c',
                  }}
                >
                  {metric.value}
                </strong>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* MES — Wafer Lots */}
      <section>
        <h2>MES — Wafer Lots</h2>

        {lotsLoading && <p>Loading wafer lots...</p>}

        {lotsError && (
          <p>Failed to load wafer lots: {lotsError}</p>
        )}

        {!lotsLoading && !lotsError && lots.length === 0 && (
          <p>No wafer lots found.</p>
        )}

        {!lotsLoading && !lotsError &&
          lots.map((lot) => (
            <div
              key={lot.lot_id}
              style={{
                padding: '12px 0',
                borderBottom: '1px solid #e2e8f0',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <strong>{lot.lot_id}</strong>
                <StatusBadge status={lot.status} />
              </div>

              <p>
                Wafers: {lot.wafer_count}
                <br />
                Route: {lot.route_id ?? 'Not assigned'}
                <br />
                Step Index: {lot.current_step_index}
              </p>
            </div>
          ))}
      </section>

      {/* Equipment Monitoring */}
      <section>
        <h2>Equipment Monitoring</h2>

        {equipmentLoading && (
          <p>Loading manufacturing equipment...</p>
        )}

        {equipmentError && (
          <p>Failed to load equipment: {equipmentError}</p>
        )}

        {!equipmentLoading &&
          !equipmentError &&
          equipment.length === 0 && (
            <p>No manufacturing equipment found.</p>
          )}

        {!equipmentLoading &&
          !equipmentError &&
          equipment.map((machine) => (
            <div
              key={machine.equipment_id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
                padding: '16px 0',
                borderBottom: '1px solid #e2e8f0',
              }}
            >
              <div>
                <strong>{machine.equipment_id}</strong>

                <p style={{ margin: '5px 0' }}>
                  Process: {machine.process_step}
                </p>

                <p style={{ margin: '5px 0' }}>
                  Assigned Lot:{' '}
                  {machine.current_lot_id ?? 'None'}
                </p>
              </div>

              <StatusBadge status={machine.status} />
            </div>
          ))}
      </section>

      {/* AMHS — Transport */}
      <section>
        <h2>AMHS — Transport</h2>

        {/* Carriers */}
        <h3
          style={{
            marginTop: '24px',
            marginBottom: '12px',
            fontSize: '16px',
          }}
        >
          Wafer Carriers ({carriers.length})
        </h3>

        {carriersLoading && <p>Loading carriers...</p>}

        {carriersError && (
          <p>Failed to load carriers: {carriersError}</p>
        )}

        {!carriersLoading &&
          !carriersError &&
          carriers.length === 0 && (
            <p>No carriers found.</p>
          )}

        {!carriersLoading &&
          !carriersError &&
          carriers.map((carrier) => (
            <div
              key={carrier.carrier_id}
              style={{
                background: '#f3f6fb',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '12px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <strong>{carrier.carrier_id}</strong>
                <StatusBadge status={carrier.status} />
              </div>

              <p style={{ marginBottom: 0 }}>
                Assigned Lot: {carrier.lot_id}
                <br />
                Current Station: {carrier.current_station}
              </p>
            </div>
          ))}

        {/* Transport Jobs */}
        <h3
          style={{
            marginTop: '28px',
            marginBottom: '12px',
            fontSize: '16px',
          }}
        >
          Transport Jobs ({jobs.length})
        </h3>

        {jobsLoading && <p>Loading transport jobs...</p>}

        {jobsError && (
          <p>Failed to load transport jobs: {jobsError}</p>
        )}

        {!jobsLoading &&
          !jobsError &&
          jobs.length === 0 && (
            <p>No transport jobs found.</p>
          )}

        {!jobsLoading &&
          !jobsError &&
          jobs.map((job) => (
            <div
              key={job.job_id}
              style={{
                background: '#f3f6fb',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '12px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '10px',
                }}
              >
                <strong>{job.job_id}</strong>
                <StatusBadge status={job.status} />
              </div>

              <p style={{ marginBottom: 0 }}>
                Carrier: {job.carrier_id}
                <br />
                From: {job.origin_station}
                <br />
                To: {job.destination_station}
                <br />
                Created: {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
          ))}
      </section>
    </main>
  )
}

export default App
