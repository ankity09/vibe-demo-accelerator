import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, Search } from 'lucide-react'
import { useApi } from '@/hooks/useApi'
import { cn } from '@/lib/utils'
import type { ColumnDef, RowAction } from '@/types'

interface DataExplorerProps {
  endpoint: string
  columns: ColumnDef[]
  searchable?: boolean
  pageSize?: number
  onRowClick?: (row: Record<string, unknown>) => void
  actions?: RowAction[]
}

type SortState = { key: string; dir: 'asc' | 'desc' } | null

const BADGE_CLASS: Record<string, string> = {
  critical: 'bg-error/10 text-error',
  error: 'bg-error/10 text-error',
  warning: 'bg-warning/10 text-warning',
  high: 'bg-warning/10 text-warning',
  success: 'bg-success/10 text-success',
  resolved: 'bg-success/10 text-success',
  active: 'bg-success/10 text-success',
  info: 'bg-info/10 text-info',
  medium: 'bg-info/10 text-info',
  pending: 'bg-info/10 text-info',
}

function getBadgeClass(value: string): string {
  return BADGE_CLASS[String(value).toLowerCase()] ?? 'bg-surface-hover text-content-muted'
}

function formatCellValue(
  value: unknown,
  type: ColumnDef['type']
): { display: string; raw: string } {
  const raw = value == null ? '' : String(value)
  if (value == null) return { display: '—', raw }
  switch (type) {
    case 'date':
      try {
        return { display: new Date(String(value)).toLocaleDateString(), raw }
      } catch {
        return { display: raw, raw }
      }
    case 'number':
      return { display: raw, raw }
    default:
      return { display: raw, raw }
  }
}

function SkeletonRows({ cols, rows = 8 }: { cols: number; rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="border-b border-border">
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <div className="h-4 bg-surface-hover rounded animate-pulse" style={{ width: `${60 + ((i + j) % 3) * 15}%` }} />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

export function DataExplorer({
  endpoint,
  columns,
  searchable = false,
  pageSize = 25,
  onRowClick,
  actions,
}: DataExplorerProps) {
  const { data, loading } = useApi<Record<string, unknown>[]>(endpoint)

  const [sort, setSort] = useState<SortState>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const colCount = columns.length + (actions && actions.length > 0 ? 1 : 0)

  const filtered = useMemo(() => {
    const rows: Record<string, unknown>[] = Array.isArray(data) ? data : []
    if (!searchable || search.trim() === '') return rows
    const q = search.trim().toLowerCase()
    return rows.filter((row) =>
      columns.some((col) => {
        const val = row[col.key]
        return val != null && String(val).toLowerCase().includes(q)
      })
    )
  }, [data, search, searchable, columns])

  const sorted = useMemo(() => {
    if (!sort) return filtered
    return [...filtered].sort((a, b) => {
      const av = a[sort.key]
      const bv = b[sort.key]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const aStr = String(av)
      const bStr = String(bv)
      const aNum = Number(av)
      const bNum = Number(bv)
      const cmp = !isNaN(aNum) && !isNaN(bNum) ? aNum - bNum : aStr.localeCompare(bStr)
      return sort.dir === 'asc' ? cmp : -cmp
    })
  }, [filtered, sort])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pageRows = sorted.slice((safePage - 1) * pageSize, safePage * pageSize)

  function toggleSort(key: string) {
    setSort((prev) => {
      if (prev?.key === key) {
        return prev.dir === 'asc' ? { key, dir: 'desc' } : null
      }
      return { key, dir: 'asc' }
    })
    setPage(1)
  }

  function handleSearch(value: string) {
    setSearch(value)
    setPage(1)
  }

  const pageWindow = useMemo(() => {
    const delta = 2
    const pages: (number | '...')[] = []
    const left = Math.max(2, safePage - delta)
    const right = Math.min(totalPages - 1, safePage + delta)

    pages.push(1)
    if (left > 2) pages.push('...')
    for (let i = left; i <= right; i++) pages.push(i)
    if (right < totalPages - 1) pages.push('...')
    if (totalPages > 1) pages.push(totalPages)

    return pages
  }, [safePage, totalPages])

  return (
    <div className="flex flex-col gap-3">
      {/* Search bar */}
      {searchable && (
        <div className="relative w-full max-w-sm">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-content-muted pointer-events-none"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search…"
            className={cn(
              'w-full pl-8 pr-3 py-1.5 text-sm rounded-md',
              'bg-surface-secondary border border-border',
              'text-content-primary placeholder:text-content-muted',
              'focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50',
              'transition-colors'
            )}
          />
        </div>
      )}

      {/* Table */}
      <div className="bg-surface-card border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-surface-secondary border-b border-border">
                {columns.map((col) => {
                  const isSorted = sort?.key === col.key
                  return (
                    <th
                      key={col.key}
                      style={col.width ? { width: col.width } : undefined}
                      className={cn(
                        'px-4 py-3 text-left text-xs font-semibold text-content-muted uppercase tracking-wide select-none',
                        col.type === 'number' && 'text-right',
                        col.sortable && 'cursor-pointer hover:text-content-primary transition-colors'
                      )}
                      onClick={col.sortable ? () => toggleSort(col.key) : undefined}
                    >
                      <div
                        className={cn(
                          'inline-flex items-center gap-1',
                          col.type === 'number' && 'flex-row-reverse w-full'
                        )}
                      >
                        {col.label}
                        {col.sortable && (
                          <span className="flex flex-col -space-y-1">
                            <ChevronUp
                              size={10}
                              className={cn(
                                isSorted && sort?.dir === 'asc'
                                  ? 'text-accent'
                                  : 'text-content-muted/40'
                              )}
                            />
                            <ChevronDown
                              size={10}
                              className={cn(
                                isSorted && sort?.dir === 'desc'
                                  ? 'text-accent'
                                  : 'text-content-muted/40'
                              )}
                            />
                          </span>
                        )}
                      </div>
                    </th>
                  )
                })}
                {actions && actions.length > 0 && (
                  <th className="px-4 py-3 text-right text-xs font-semibold text-content-muted uppercase tracking-wide w-px whitespace-nowrap">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonRows cols={colCount} />
              ) : pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={colCount}
                    className="px-4 py-12 text-center text-content-muted text-sm"
                  >
                    No data found
                  </td>
                </tr>
              ) : (
                pageRows.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className={cn(
                      'border-b border-border last:border-0 transition-colors',
                      onRowClick && 'hover:bg-surface-hover cursor-pointer'
                    )}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                  >
                    {columns.map((col) => {
                      const raw = row[col.key]
                      const { display } = formatCellValue(raw, col.type)

                      if (col.type === 'badge') {
                        return (
                          <td key={col.key} className="px-4 py-3">
                            <span
                              className={cn(
                                'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                                getBadgeClass(display)
                              )}
                            >
                              {display}
                            </span>
                          </td>
                        )
                      }

                      if (col.type === 'link') {
                        return (
                          <td key={col.key} className="px-4 py-3">
                            <a
                              href={String(raw ?? '#')}
                              className="text-info underline underline-offset-2 hover:text-info/80 transition-colors"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {display}
                            </a>
                          </td>
                        )
                      }

                      if (col.type === 'number') {
                        return (
                          <td
                            key={col.key}
                            className="px-4 py-3 text-right font-mono text-content-primary"
                          >
                            {display}
                          </td>
                        )
                      }

                      if (col.type === 'date') {
                        return (
                          <td key={col.key} className="px-4 py-3 text-content-secondary">
                            {display}
                          </td>
                        )
                      }

                      // default: text
                      return (
                        <td key={col.key} className="px-4 py-3 text-content-primary">
                          {display}
                        </td>
                      )
                    })}

                    {actions && actions.length > 0 && (
                      <td
                        className="px-4 py-3 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="inline-flex items-center gap-1 justify-end">
                          {actions.map((action) => {
                            const Icon = action.icon
                            return (
                              <button
                                key={action.label}
                                title={action.label}
                                onClick={() => action.onClick(row)}
                                className={cn(
                                  'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors',
                                  action.variant === 'destructive'
                                    ? 'text-error hover:bg-error/10'
                                    : 'text-content-muted hover:bg-surface-hover hover:text-content-primary'
                                )}
                              >
                                {Icon && <Icon size={12} />}
                                <span>{action.label}</span>
                              </button>
                            )
                          })}
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {!loading && sorted.length > pageSize && (
        <div className="flex items-center justify-between text-sm text-content-muted">
          <span>
            {sorted.length === 0
              ? 'No results'
              : `${(safePage - 1) * pageSize + 1}–${Math.min(safePage * pageSize, sorted.length)} of ${sorted.length}`}
          </span>
          <div className="flex items-center gap-1">
            <button
              disabled={safePage === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-2 py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors"
            >
              ‹ Prev
            </button>

            {pageWindow.map((p, i) =>
              p === '...' ? (
                <span key={`ellipsis-${i}`} className="px-1">
                  …
                </span>
              ) : (
                <button
                  key={p}
                  onClick={() => setPage(p as number)}
                  className={cn(
                    'min-w-[2rem] px-2 py-1 rounded text-sm transition-colors',
                    p === safePage
                      ? 'bg-accent text-white font-medium'
                      : 'hover:bg-surface-hover'
                  )}
                >
                  {p}
                </button>
              )
            )}

            <button
              disabled={safePage === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-2 py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors"
            >
              Next ›
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
