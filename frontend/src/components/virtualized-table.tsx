/**
 * Virtualized Table Component
 *
 * High-performance table component for large datasets using virtual scrolling.
 * Optimized for real-time data updates like CAN messages.
 */

import React, { useMemo, useRef, useEffect, useState } from 'react'
import { FixedSizeList as List, ListChildComponentProps } from 'react-window'
// Table components not needed for virtualized implementation
import { Skeleton } from '@/components/ui/skeleton'

export interface VirtualizedTableColumn<T> {
  id: string
  header: string
  accessor: (item: T) => React.ReactNode
  width?: number
  className?: string
}

export interface VirtualizedTableProps<T> {
  data: T[]
  columns: VirtualizedTableColumn<T>[]
  height?: number
  itemHeight?: number
  className?: string
  isLoading?: boolean
  loadingRows?: number
  emptyMessage?: string
  getRowKey: (item: T, index: number) => string
  onRowClick?: (item: T, index: number) => void
  stickyHeader?: boolean
}

// Row component for virtualized list
function VirtualizedRow<T>({
  index,
  style,
  data
}: ListChildComponentProps & {
  data: {
    items: T[]
    columns: VirtualizedTableColumn<T>[]
    getRowKey: (item: T, index: number) => string
    onRowClick?: (item: T, index: number) => void
  }
}) {
  const { items, columns, onRowClick } = data
  const item = items[index]

  if (!item) {
    return (
      <div style={style} className="flex">
        {columns.map((column) => (
          <div
            key={column.id}
            className="flex-1 p-2 border-b flex items-center"
            style={{ width: column.width }}
          >
            <Skeleton className="h-4 w-full" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div
      style={style}
      className={`flex border-b hover:bg-muted/50 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
      onClick={onRowClick ? () => onRowClick(item, index) : undefined}
      onKeyDown={onRowClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onRowClick(item, index)
        }
      } : undefined}
      tabIndex={onRowClick ? 0 : -1}
      role={onRowClick ? 'button' : undefined}
    >
      {columns.map((column) => (
        <div
          key={column.id}
          className={`flex-1 p-2 flex items-center text-sm ${column.className || ''}`}
          style={{ width: column.width }}
        >
          {column.accessor(item)}
        </div>
      ))}
    </div>
  )
}

// Loading skeleton component
function LoadingSkeleton<T>({
  columns,
  rows = 10
}: {
  columns: VirtualizedTableColumn<T>[]
  rows?: number
}) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex">
          {columns.map((column) => (
            <div
              key={column.id}
              className="flex-1 p-2 flex items-center"
              style={{ width: column.width }}
            >
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export function VirtualizedTable<T>({
  data,
  columns,
  height = 400,
  itemHeight = 48,
  className = '',
  isLoading = false,
  loadingRows = 10,
  emptyMessage = 'No data available',
  getRowKey,
  onRowClick,
  stickyHeader = true
}: VirtualizedTableProps<T>) {
  const listRef = useRef<List>(null)
  const [containerWidth, setContainerWidth] = useState<number>(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Update container width on resize
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.clientWidth)
      }
    }

    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  // Scroll to bottom when new data arrives (for real-time feeds)
  useEffect(() => {
    if (listRef.current && data.length > 0) {
      // Only auto-scroll if we're near the bottom (within last 5 items)
      const scrollOffset = listRef.current.scrollTop || 0
      const maxScroll = (data.length - 1) * itemHeight - height
      const nearBottom = scrollOffset >= maxScroll - (5 * itemHeight)

      if (nearBottom) {
        listRef.current.scrollToItem(data.length - 1, 'end')
      }
    }
  }, [data.length, itemHeight, height])

  // Memoize list data to prevent unnecessary re-renders
  const listData = useMemo(() => ({
    items: data,
    columns,
    getRowKey,
    onRowClick
  }), [data, columns, getRowKey, onRowClick])

  if (isLoading && data.length === 0) {
    return (
      <div className={`rounded-md border ${className}`}>
        <div className="overflow-hidden">
          {/* Header */}
          <div className="flex bg-muted/50 border-b">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex-1 p-3 text-sm font-medium text-left"
                style={{ width: column.width }}
              >
                {column.header}
              </div>
            ))}
          </div>

          {/* Loading Content */}
          <div className="p-4">
            <LoadingSkeleton columns={columns} rows={loadingRows} />
          </div>
        </div>
      </div>
    )
  }

  if (!isLoading && data.length === 0) {
    return (
      <div className={`rounded-md border ${className}`}>
        <div className="overflow-hidden">
          {/* Header */}
          <div className="flex bg-muted/50 border-b">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex-1 p-3 text-sm font-medium text-left"
                style={{ width: column.width }}
              >
                {column.header}
              </div>
            ))}
          </div>

          {/* Empty State */}
          <div className="p-12 text-center">
            <p className="text-sm text-muted-foreground">{emptyMessage}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={`rounded-md border ${className}`}>
      <div className="overflow-hidden">
        {/* Sticky Header */}
        {stickyHeader && (
          <div className="flex bg-muted/50 border-b sticky top-0 z-10">
            {columns.map((column) => (
              <div
                key={column.id}
                className="flex-1 p-3 text-sm font-medium text-left"
                style={{ width: column.width }}
              >
                {column.header}
              </div>
            ))}
          </div>
        )}

        {/* Virtualized Content */}
        <List
          ref={listRef}
          height={height}
          itemCount={data.length}
          itemSize={itemHeight}
          itemData={listData}
          width={containerWidth || '100%'}
          overscanCount={5} // Render 5 extra items above/below viewport
        >
          {VirtualizedRow}
        </List>
      </div>
    </div>
  )
}
