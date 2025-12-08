import { useState, useRef, useEffect, ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface TooltipProps {
  content: ReactNode
  children: ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
  className?: string
}

export function Tooltip({
  content,
  children,
  position = 'top',
  delay = 200,
  className = '',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [coords, setCoords] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect()
        const scrollX = window.scrollX
        const scrollY = window.scrollY

        let x = rect.left + scrollX + rect.width / 2
        let y = rect.top + scrollY

        switch (position) {
          case 'bottom':
            y = rect.bottom + scrollY + 8
            break
          case 'left':
            x = rect.left + scrollX - 8
            y = rect.top + scrollY + rect.height / 2
            break
          case 'right':
            x = rect.right + scrollX + 8
            y = rect.top + scrollY + rect.height / 2
            break
          case 'top':
          default:
            y = rect.top + scrollY - 8
            break
        }

        setCoords({ x, y })
        setIsVisible(true)
      }
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    setIsVisible(false)
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // Adjust position if tooltip would go off screen
  useEffect(() => {
    if (isVisible && tooltipRef.current) {
      const tooltip = tooltipRef.current
      const rect = tooltip.getBoundingClientRect()

      let newX = coords.x
      let newY = coords.y

      // Keep tooltip within viewport
      if (rect.right > window.innerWidth) {
        newX -= rect.right - window.innerWidth + 10
      }
      if (rect.left < 0) {
        newX -= rect.left - 10
      }
      if (rect.bottom > window.innerHeight) {
        newY -= rect.bottom - window.innerHeight + 10
      }
      if (rect.top < 0) {
        newY -= rect.top - 10
      }

      if (newX !== coords.x || newY !== coords.y) {
        setCoords({ x: newX, y: newY })
      }
    }
  }, [isVisible, coords])

  const getPositionStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'absolute',
      zIndex: 9999,
    }

    switch (position) {
      case 'bottom':
        return { ...base, left: coords.x, top: coords.y, transform: 'translateX(-50%)' }
      case 'left':
        return { ...base, left: coords.x, top: coords.y, transform: 'translate(-100%, -50%)' }
      case 'right':
        return { ...base, left: coords.x, top: coords.y, transform: 'translateY(-50%)' }
      case 'top':
      default:
        return { ...base, left: coords.x, top: coords.y, transform: 'translate(-50%, -100%)' }
    }
  }

  const tooltipElement = isVisible && typeof document !== 'undefined' ? createPortal(
    <div
      ref={tooltipRef}
      style={getPositionStyles()}
      className={`px-2 py-1 text-xs font-medium bg-zinc-900 text-zinc-100 rounded border border-zinc-700 shadow-lg whitespace-nowrap pointer-events-none animate-in fade-in-0 zoom-in-95 duration-100 ${className}`}
      role="tooltip"
    >
      {content}
    </div>,
    document.body
  ) : null

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-flex"
      >
        {children}
      </div>
      {tooltipElement}
    </>
  )
}

export default Tooltip
