/**
 * Hook for managing virtualized table state
 */
import { useState, useEffect, useRef } from 'react'

export function useVirtualizedTable<T>({
  data,
  maxItems = 1000,
  autoScroll = true
}: {
  data: T[]
  maxItems?: number
  autoScroll?: boolean
}) {
  const [filteredData, setFilteredData] = useState<T[]>([])
  const [visibleData, setVisibleData] = useState<T[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Update filtered data when input data changes
  useEffect(() => {
    setFilteredData(data.slice(-maxItems))
  }, [data, maxItems])

  // Update visible data when filtered data or current index changes
  useEffect(() => {
    const startIndex = Math.max(0, currentIndex)
    const endIndex = Math.min(filteredData.length, startIndex + 50) // Show 50 items at a time
    setVisibleData(filteredData.slice(startIndex, endIndex))
  }, [filteredData, currentIndex])

  // Auto-scroll to bottom when new data arrives
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      setCurrentIndex(Math.max(0, filteredData.length - 50))
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [filteredData.length, autoScroll])

  const scrollToIndex = (index: number) => {
    setCurrentIndex(Math.max(0, Math.min(index, filteredData.length - 50)))
  }

  const scrollToTop = () => scrollToIndex(0)
  const scrollToBottom = () => scrollToIndex(filteredData.length - 50)

  return {
    visibleData,
    totalItems: filteredData.length,
    currentIndex,
    containerRef,
    scrollToIndex,
    scrollToTop,
    scrollToBottom,
    hasMore: currentIndex + 50 < filteredData.length,
    hasPrevious: currentIndex > 0
  }
}
