import { clsx } from 'clsx'

export type ProductSubtype =
  // Boxes
  | 'Collector Booster Box'
  | 'Case'
  | 'Box'
  // Bundles
  | 'Play Bundle'
  | 'Blaster Box'
  | 'Serialized Advantage'
  | 'Starter Set'
  | 'Bundle'
  // Packs
  | 'Collector Booster Pack'
  | 'Play Booster Pack'
  | 'Silver Pack'
  | 'Pack'
  // Lots
  | 'Lot'
  | 'Bulk'

interface ProductSubtypeBadgeProps {
  subtype: string
  size?: 'xs' | 'sm' | 'md'
  className?: string
}

// Simple solid color styles for each subtype category
const SUBTYPE_STYLES: Record<string, { bg: string; text: string }> = {
  // === BOXES (Blue tones) ===
  'Collector Booster Box': {
    bg: 'bg-blue-600',
    text: 'text-white',
  },
  'Case': {
    bg: 'bg-blue-800',
    text: 'text-white',
  },
  'Box': {
    bg: 'bg-blue-500',
    text: 'text-white',
  },

  // === BUNDLES (Teal/Cyan tones) ===
  'Play Bundle': {
    bg: 'bg-teal-600',
    text: 'text-white',
  },
  'Blaster Box': {
    bg: 'bg-teal-500',
    text: 'text-white',
  },
  'Serialized Advantage': {
    bg: 'bg-cyan-600',
    text: 'text-white',
  },
  'Starter Set': {
    bg: 'bg-teal-700',
    text: 'text-white',
  },
  'Bundle': {
    bg: 'bg-teal-500',
    text: 'text-white',
  },

  // === PACKS (Indigo/Purple tones) ===
  'Collector Booster Pack': {
    bg: 'bg-indigo-600',
    text: 'text-white',
  },
  'Play Booster Pack': {
    bg: 'bg-indigo-500',
    text: 'text-white',
  },
  'Silver Pack': {
    bg: 'bg-slate-500',
    text: 'text-white',
  },
  'Pack': {
    bg: 'bg-indigo-400',
    text: 'text-white',
  },

  // === LOTS (Gray tones) ===
  'Lot': {
    bg: 'bg-zinc-600',
    text: 'text-white',
  },
  'Bulk': {
    bg: 'bg-zinc-500',
    text: 'text-white',
  },
}

// Fallback style
const DEFAULT_STYLE = {
  bg: 'bg-gray-500',
  text: 'text-white',
}

// Size variants
const SIZE_CLASSES = {
  xs: 'text-[10px] px-1.5 py-0.5',
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
}

export function ProductSubtypeBadge({ subtype, size = 'sm', className }: ProductSubtypeBadgeProps) {
  const style = SUBTYPE_STYLES[subtype] || DEFAULT_STYLE

  return (
    <span
      className={clsx(
        'inline-block rounded font-medium',
        SIZE_CLASSES[size],
        style.bg,
        style.text,
        className
      )}
    >
      {subtype}
    </span>
  )
}

// Helper to get just the classes (for use in tables)
export function getSubtypeClasses(subtype: string, size: 'xs' | 'sm' | 'md' = 'sm'): string {
  const style = SUBTYPE_STYLES[subtype] || DEFAULT_STYLE

  return clsx(
    'inline-block rounded font-medium',
    SIZE_CLASSES[size],
    style.bg,
    style.text
  )
}

// Hex colors for charts (matching Tailwind classes above)
const SUBTYPE_HEX_COLORS: Record<string, string> = {
  // Boxes (Blue)
  'Collector Booster Box': '#2563eb', // blue-600
  'Case': '#1e40af',                  // blue-800
  'Box': '#3b82f6',                   // blue-500
  // Bundles (Teal/Cyan)
  'Play Bundle': '#0d9488',           // teal-600
  'Blaster Box': '#14b8a6',           // teal-500
  'Serialized Advantage': '#0891b2',  // cyan-600
  'Starter Set': '#0f766e',           // teal-700
  'Bundle': '#14b8a6',                // teal-500
  // Packs (Indigo/Purple)
  'Collector Booster Pack': '#4f46e5', // indigo-600
  'Play Booster Pack': '#6366f1',      // indigo-500
  'Silver Pack': '#64748b',            // slate-500
  'Pack': '#818cf8',                   // indigo-400
  // Lots (Gray)
  'Lot': '#52525b',                    // zinc-600
  'Bulk': '#71717a',                   // zinc-500
}

// Get hex color for chart use
export function getSubtypeColor(subtype: string | undefined | null): string {
  if (!subtype) return '#6b7280' // gray-500 fallback
  return SUBTYPE_HEX_COLORS[subtype] || '#6b7280'
}

export default ProductSubtypeBadge
