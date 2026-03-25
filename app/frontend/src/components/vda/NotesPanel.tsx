import { useState } from 'react'
import { X } from 'lucide-react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import { timeAgo } from '@/lib/utils'

interface Note {
  id: string | number
  note_text: string
  author: string
  created_at: string
}

interface NotesPanelProps {
  entityType: string
  entityId: string
  endpoint?: string
  open: boolean
  onClose: () => void
}

export function NotesPanel({
  entityType,
  entityId,
  endpoint = '/api/notes',
  open,
  onClose,
}: NotesPanelProps) {
  const [noteText, setNoteText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { data, loading, refetch } = useApi<Note[]>(endpoint, {
    autoFetch: open,
    params: { entity_type: entityType, entity_id: entityId },
  })

  const notes = data ?? []

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = noteText.trim()
    if (!text) return

    setSubmitting(true)
    try {
      await api.post(endpoint, {
        entity_type: entityType,
        entity_id: entityId,
        note_text: text,
        author: 'user',
      })
      setNoteText('')
      await refetch()
    } catch (err) {
      console.error('Failed to submit note:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={[
          'fixed top-0 right-0 h-full w-96 z-50',
          'bg-surface-primary border-l border-border',
          'flex flex-col',
          'transition-transform duration-200',
          open ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
        role="dialog"
        aria-modal="true"
        aria-label="Notes panel"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
          <h2 className="text-content-primary font-semibold text-sm">Notes</h2>
          <button
            onClick={onClose}
            className="text-content-muted hover:text-content-primary transition-colors p-1 rounded"
            aria-label="Close notes panel"
          >
            <X size={16} />
          </button>
        </div>

        {/* Notes list */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          {loading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse space-y-1">
                  <div className="h-3 bg-surface-hover rounded w-3/4" />
                  <div className="h-3 bg-surface-hover rounded w-1/2" />
                  <div className="h-2 bg-surface-hover rounded w-1/4 mt-1" />
                </div>
              ))}
            </div>
          )}

          {!loading && notes.length === 0 && (
            <p className="text-content-muted text-xs text-center py-6">
              No notes yet. Add one below.
            </p>
          )}

          {!loading &&
            notes.map((note) => (
              <div
                key={note.id}
                className="bg-surface-card border border-border rounded-lg p-3 space-y-1"
              >
                <p className="text-content-primary text-sm leading-relaxed">
                  {note.note_text}
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-content-muted text-xs">{note.author}</span>
                  <span className="text-content-muted text-xs opacity-50">·</span>
                  <span className="text-content-muted text-xs">
                    {timeAgo(note.created_at)}
                  </span>
                </div>
              </div>
            ))}
        </div>

        {/* Add note form */}
        <form
          onSubmit={handleSubmit}
          className="border-t border-border px-4 py-3 flex-shrink-0 space-y-2"
        >
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add a note..."
            rows={3}
            className={[
              'w-full resize-none rounded-lg px-3 py-2',
              'bg-surface-card border border-border',
              'text-content-primary text-sm placeholder:text-content-muted',
              'focus:outline-none focus:ring-1 focus:ring-accent',
              'transition-colors',
            ].join(' ')}
          />
          <button
            type="submit"
            disabled={submitting || !noteText.trim()}
            className={[
              'w-full rounded-lg px-3 py-1.5 text-xs font-medium',
              'bg-accent text-white',
              'hover:opacity-90 transition-opacity',
              'disabled:opacity-40 disabled:cursor-not-allowed',
            ].join(' ')}
          >
            {submitting ? 'Saving...' : 'Add Note'}
          </button>
        </form>
      </div>
    </>
  )
}
