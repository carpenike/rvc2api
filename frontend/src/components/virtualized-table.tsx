/**
 * Virtualized Table Component
 *
 * High-performance table component for large datasets using virtual scrolling.
 * Optimized for real-time data updates like CAN messages.
 */

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { FixedSizeList as List } from 'react-window'
// Table components not needed for virtualized implementation
import { Skeleton } from '@/components/ui/skeleton'

// Type definition for react-window list child component props
interface ListChildComponentProps<T = unknown> {
  index: number
  style: React.CSSProperties
  data: T
}

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
}: ListChildComponentProps<{
  items: T[]
  columns: VirtualizedTableColumn<T>[]
  getRowKey: (item: T, index: number) => string
  onRowClick?: (item: T, index: number) => void
}>) {
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

  return onRowClick ? (
    <button
      style={style}
      className="flex border-b hover:bg-muted/50 transition-colors cursor-pointer w-full text-left"
      onClick={() => onRowClick(item, index)}
      type="button"
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
    </button>
  ) : (
    <div
      style={style}
      className="flex border-b hover:bg-muted/50 transition-colors"
      role="row"
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
      // Auto-scroll to the bottom for new data (simplified approach)
      listRef.current.scrollToItem(data.length - 1, 'end')
    }
  }, [data.length])

  // Memoize list data to prevent unnecessary re-renders
  const listData = useMemo(() => {
    const listItemData = {
      items: data,
      columns,
      getRowKey,
    } as { items: T[]; columns: VirtualizedTableColumn<T>[]; getRowKey: (item: T, index: number) => string; onRowClick?: (item: T, index: number) => void }

    if (onRowClick) {
      listItemData.onRowClick = onRowClick
    }

    return listItemData
  }, [data, columns, getRowKey, onRowClick])

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
          {VirtualizedRow<T>}
        </List>
      </div>
    </div>
  )
}
