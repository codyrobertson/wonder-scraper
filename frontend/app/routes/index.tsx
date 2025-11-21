import { createRoute, redirect, useNavigate, Link } from '@tanstack/react-router'
import { auth } from '../utils/auth'
import { api } from '../utils/auth'
import { useQuery } from '@tanstack/react-query'
import { ColumnDef, flexRender, getCoreRowModel, useReactTable, getSortedRowModel, SortingState, getFilteredRowModel } from '@tanstack/react-table'
import { useState, useMemo } from 'react'
import { ArrowUpDown, Search, ArrowUp, ArrowDown, LayoutDashboard, LineChart, Wallet, Settings, User, Server } from 'lucide-react'
import clsx from 'clsx'
import { Route as rootRoute } from './__root'

// Updated Type Definition including placeholder fields
type Card = {
  id: number
  name: string
  set_name: string
  rarity_id: number
  rarity_name?: string
  // Optional fields that might come from backend logic or joins
  latest_price?: number
  volume_24h?: number
  price_delta_24h?: number // Placeholder for delta
  lowest_ask?: number
  inventory?: number
  volume_usd_24h?: number // New field for dollar volume
  highest_bid?: number
}

type UserProfile = {
    id: number
    email: string
    is_superuser: boolean
}

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Home,
})

function Home() {
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [rarityFilter, setRarityFilter] = useState('all')
  const [setFilter, setSetFilter] = useState('all')
  const [hasBidOnly, setHasBidOnly] = useState(false)
  const [hasInventoryOnly, setHasInventoryOnly] = useState(false)
  const [hideZeroRows, setHideZeroRows] = useState(true)
  const [minVolume, setMinVolume] = useState(0)
  const navigate = useNavigate()

  // Fetch User Profile for Permissions
  const { data: user } = useQuery({
      queryKey: ['me'],
      queryFn: async () => {
          try {
              return await api.get('users/me').json<UserProfile>()
          } catch {
              return null
          }
      },
      retry: false
  })

  const { data: cards, isLoading } = useQuery({
    queryKey: ['cards', 'full'],
    queryFn: async () => {
      const data = await api.get('cards?limit=100&hide_zero=false').json<Card[]>()
      return data.map(c => ({
          ...c,
          rarity_name: c.rarity_name ?? 'Unknown',
          latest_price: c.latest_price ?? 0,
          volume_24h: c.volume_24h ?? 0,
          inventory: c.inventory ?? 0,
          lowest_ask: c.lowest_ask ?? 0,
          highest_bid: c.highest_bid ?? 0,
          price_delta_24h: c.price_delta_24h ?? 0,
          volume_usd_24h: (c.volume_24h ?? 0) * (c.latest_price ?? 0),
      }))
    }
  })

  const uniqueRarities = useMemo(() => {
    if (!cards) return []
    return Array.from(new Set(cards.map(c => c.rarity_name).filter(Boolean))).sort()
  }, [cards])

  const uniqueSets = useMemo(() => {
    if (!cards) return []
    return Array.from(new Set(cards.map(c => c.set_name).filter(Boolean))).sort()
  }, [cards])

  const filteredCards = useMemo(() => {
    if (!cards) return []
    return cards.filter(card => {
        const hasSignal = (
            (card.latest_price ?? 0) > 0 ||
            (card.volume_24h ?? 0) > 0 ||
            (card.inventory ?? 0) > 0 ||
            (card.highest_bid ?? 0) > 0
        )

        if (hideZeroRows && !hasSignal) {
            return false
        }
        if (rarityFilter !== 'all' && card.rarity_name !== rarityFilter) {
            return false
        }
        if (setFilter !== 'all' && card.set_name !== setFilter) {
            return false
        }
        if (hasBidOnly && (card.highest_bid ?? 0) <= 0) {
            return false
        }
        if (hasInventoryOnly && (card.inventory ?? 0) <= 0) {
            return false
        }
        if (minVolume > 0 && (card.volume_24h ?? 0) < minVolume) {
            return false
        }

        return true
    })
  }, [cards, hideZeroRows, rarityFilter, setFilter, hasBidOnly, hasInventoryOnly, minVolume])

  const columns = useMemo<ColumnDef<Card>[]>(() => [
    {
      accessorKey: 'name',
      header: ({ column }) => {
        return (
          <button
            className="flex items-center gap-1 hover:text-primary uppercase tracking-wider text-xs"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Name
            <ArrowUpDown className="h-3 w-3" />
          </button>
        )
      },
      cell: ({ row }) => (
        <div>
            <div className="font-bold text-foreground">{row.getValue('name')}</div>
            <div className="text-xs text-muted-foreground uppercase">{row.original.set_name}</div>
        </div>
      ),
    },
    {
      accessorKey: 'latest_price',
      header: ({ column }) => (
        <div className="text-right uppercase tracking-wider text-xs">Price</div>
      ),
      cell: ({ row }) => {
          const price = row.original.latest_price
          const delta = row.original.price_delta_24h || 0
          const isPositive = delta >= 0
          const hasPrice = price && price > 0

          return (
            <div className="text-right">
                <div className="font-mono text-base">
                    {hasPrice ? `$${price.toFixed(2)}` : '---'}
                </div>
                {hasPrice && delta !== 0 ? (
                    <div className={clsx(
                        "text-xs font-mono flex items-center justify-end gap-1",
                        isPositive ? "text-emerald-500" : "text-red-500" // Updated to solid colors
                    )}>
                        {isPositive ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                        {Math.abs(delta).toFixed(2)}%
                    </div>
                ) : <div className="text-xs text-muted-foreground/30">-</div>}
            </div>
          )
      }
    },
    {
        accessorKey: 'volume_24h',
        header: () => <div className="text-right uppercase tracking-wider text-xs">Vol (Units)</div>,
        cell: ({ row }) => {
            const vol = row.original.volume_24h || 0
            // Improved Contrast Badges
            let badgeClass = "bg-zinc-800 text-zinc-300 border-zinc-700" // Low/Gray
            if (vol > 30) badgeClass = "bg-emerald-700 text-emerald-50 border-emerald-600 font-bold" // Updated to solid colors
            else if (vol > 10) badgeClass = "bg-amber-700 text-amber-50 border-amber-600 font-bold" // Updated to solid colors
            else if (vol === 0) badgeClass = "bg-red-700 text-red-50 border-red-600 opacity-50" // Updated to solid colors

            return (
                <div className="flex justify-end">
                    <span className={clsx("px-2 py-0.5 rounded border font-mono text-xs shadow-sm", badgeClass)}>
                        {vol}
                    </span>
                </div>
            )
        }
    },
    {
        accessorKey: 'volume_usd_24h', // New column for dollar volume
        header: () => <div className="text-right uppercase tracking-wider text-xs">Vol ($)</div>,
        cell: ({ row }) => {
            const volUsd = row.original.volume_usd_24h || 0
            return (
                <div className="text-right font-mono text-xs text-muted-foreground">
                    {volUsd > 0 ? `$${volUsd.toFixed(2)}` : '---'}
                </div>
            )
        }
    },
    {
        accessorKey: 'lowest_ask',
        header: () => <div className="text-right uppercase tracking-wider text-xs text-muted-foreground">Low Ask</div>,
        cell: ({ row }) => {
            const lowAsk = row.original.lowest_ask ?? 0
            return (
                <div className="text-right font-mono text-xs text-muted-foreground">
                    {lowAsk > 0 ? `$${lowAsk.toFixed(2)}` : '---'}
                </div>
            )
        }
    },
    {
        accessorKey: 'highest_bid',
        header: () => <div className="text-right uppercase tracking-wider text-xs text-muted-foreground">High Bid</div>,
        cell: ({ row }) => {
            const bid = row.original.highest_bid ?? 0
            return (
                <div className="text-right font-mono text-xs text-muted-foreground">
                    {bid > 0 ? `$${bid.toFixed(2)}` : '---'}
                </div>
            )
        }
    },
    {
        accessorKey: 'inventory',
        header: () => <div className="text-right uppercase tracking-wider text-xs text-muted-foreground">Inv</div>,
        cell: ({ row }) => (
            <div className="text-right font-mono text-xs text-muted-foreground">
                {row.original.inventory ?? 0}
            </div>
        )
    }
  ], [])

  const table = useReactTable({
    data: filteredCards || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      globalFilter,
    },
  })

  // Compute dynamic sidebars
  const topMovers = useMemo(() => {
      if (!filteredCards.length) return []
      // Filter items with price > 0 and sort by delta desc
      return [...filteredCards]
          .filter(c => (c.latest_price || 0) > 0)
          .sort((a, b) => (b.price_delta_24h || 0) - (a.price_delta_24h || 0))
          .slice(0, 5)
  }, [filteredCards])

  const topVolume = useMemo(() => {
      if (!filteredCards.length) return []
      return [...filteredCards]
          .sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0))
          .slice(0, 5)
  }, [filteredCards])

  return (
    <div className="p-4 min-h-screen bg-background text-foreground font-mono">
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-6 border-b border-border pb-4">
        <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight uppercase">Wonder Scraper <span className="text-xs font-normal text-muted-foreground bg-muted px-1 rounded">BETA</span></h1>
        </div>
        
        <div className="relative w-96">
             <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
             <input 
                type="text" 
                placeholder="SEARCH (CMD+K)" 
                className="w-full bg-muted/50 pl-9 pr-4 py-2 rounded border border-border text-sm focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-muted-foreground/50"
                value={globalFilter}
                onChange={e => setGlobalFilter(e.target.value)}
             />
        </div>
        
        <div className="flex gap-4 items-center">
            <div className="text-xs text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-green-500 inline-block mr-2"></span>
                System Online
            </div>
            {user ? (
                <>
                    <div className="h-4 w-px bg-border"></div>
                    <div className="text-xs font-bold uppercase">{user.email}</div>
                    <button onClick={() => auth.logout()} className="text-xs uppercase hover:text-primary transition-colors text-muted-foreground">Logout</button>
                </>
            ) : (
                <>
                    <div className="h-4 w-px bg-border"></div>
                    <Link to="/login" className="text-xs uppercase hover:text-primary transition-colors text-muted-foreground font-bold">Login</Link>
                </>
            )}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Sidebar */}
        <div className="col-span-2 border-r border-border pr-4 hidden md:block h-[calc(100vh-100px)] sticky top-20">
            <nav className="space-y-1">
                <Link to="/" className="flex items-center gap-3 px-3 py-2 bg-muted/50 text-foreground rounded border border-border text-xs font-bold uppercase">
                    <LayoutDashboard className="w-4 h-4" />
                    <span>Dashboard</span>
                </Link>
                <Link to="/market" className="flex items-center gap-3 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-muted/30 rounded transition-colors text-xs uppercase">
                    <LineChart className="w-4 h-4" />
                    Market Analysis
                </Link>
                <Link to="/portfolio" className="flex items-center gap-3 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-muted/30 rounded transition-colors text-xs uppercase">
                    <Wallet className="w-4 h-4" />
                    Portfolio
                </Link>
                <Link to="/profile" className="flex items-center gap-3 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-muted/30 rounded transition-colors text-xs uppercase">
                    <User className="w-4 h-4" />
                    Profile
                </Link>
                
                {/* Admin Only Section */}
                {user?.is_superuser && (
                    <>
                        <div className="pt-6 pb-2 text-[10px] uppercase text-muted-foreground font-bold tracking-widest border-t border-border mt-4">System Admin</div>
                        <a href="#" className="flex items-center gap-3 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-muted/30 rounded transition-colors text-xs uppercase">
                            <Server className="w-4 h-4" />
                            Scraper Status
                        </a>
                        <a href="#" className="flex items-center gap-3 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-muted/30 rounded transition-colors text-xs uppercase">
                            <Settings className="w-4 h-4" />
                            Settings
                        </a>
                    </>
                )}
            </nav>
        </div>
        
        {/* Main Content */}
        <div className="col-span-12 md:col-span-8">
             <div className="border border-border rounded bg-card overflow-hidden">
                <div className="border-b border-border bg-muted/20 p-4 space-y-4">
                    <div className="flex flex-wrap items-center justify-between text-[10px] uppercase text-muted-foreground">
                        <span className="font-bold tracking-[0.3em]">Market Filters</span>
                        <span>{filteredCards.length} / {cards?.length ?? 0} cards visible</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <label className="flex flex-col gap-1 text-[10px] uppercase text-muted-foreground font-bold tracking-widest">
                            Rarity
                            <select 
                                value={rarityFilter}
                                onChange={(e) => setRarityFilter(e.target.value)}
                                className="bg-background border border-border rounded px-2 py-1 text-xs uppercase focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                                <option value="all">All Rarities</option>
                                {uniqueRarities.map(r => (
                                    <option key={r} value={r}>{r}</option>
                                ))}
                            </select>
                        </label>
                        <label className="flex flex-col gap-1 text-[10px] uppercase text-muted-foreground font-bold tracking-widest">
                            Set
                            <select 
                                value={setFilter}
                                onChange={(e) => setSetFilter(e.target.value)}
                                className="bg-background border border-border rounded px-2 py-1 text-xs uppercase focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                                <option value="all">All Sets</option>
                                {uniqueSets.map(set => (
                                    <option key={set} value={set}>{set}</option>
                                ))}
                            </select>
                        </label>
                        <label className="flex flex-col gap-1 text-[10px] uppercase text-muted-foreground font-bold tracking-widest">
                            Min Volume
                            <input 
                                type="number"
                                min={0}
                                value={minVolume}
                                onChange={(e) => setMinVolume(Math.max(0, Number(e.target.value) || 0))}
                                className="bg-background border border-border rounded px-2 py-1 text-xs uppercase focus:outline-none focus:ring-1 focus:ring-primary"
                            />
                        </label>
                    </div>
                    <div className="flex flex-wrap gap-4 text-[11px] uppercase text-muted-foreground">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" className="accent-primary" checked={hideZeroRows} onChange={(e) => setHideZeroRows(e.target.checked)} />
                            Hide Zero Data
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" className="accent-primary" checked={hasBidOnly} onChange={(e) => setHasBidOnly(e.target.checked)} />
                            Has Bids
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" className="accent-primary" checked={hasInventoryOnly} onChange={(e) => setHasInventoryOnly(e.target.checked)} />
                            Has Inventory
                        </label>
                    </div>
                </div>
                {isLoading ? (
                    <div className="p-12 text-center">
                        <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                        <div className="text-xs uppercase text-muted-foreground animate-pulse">Loading market stream...</div>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs uppercase bg-muted/30 text-muted-foreground border-b border-border">
                                {table.getHeaderGroups().map(headerGroup => (
                                    <tr key={headerGroup.id}>
                                        {headerGroup.headers.map(header => (
                                            <th key={header.id} className="px-4 py-3 font-medium">
                                                {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                                            </th>
                                        ))}
                                    </tr>
                                ))}
                            </thead>
                            <tbody className="divide-y divide-border/50">
                                {table.getRowModel().rows?.length ? (
                                    table.getRowModel().rows.map(row => (
                                        <tr 
                                            key={row.id} 
                                            className="hover:bg-muted/30 transition-colors cursor-pointer group"
                                            onClick={() => navigate({ to: '/cards/$cardId', params: { cardId: String(row.original.id) } })}
                                        >
                                            {row.getVisibleCells().map(cell => (
                                                <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                                                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                                </td>
                                            ))}
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={columns.length} className="h-32 text-center text-muted-foreground text-xs uppercase">
                                            No market data found.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
             </div>
        </div>

        {/* Right Sidebar */}
        <div className="col-span-12 md:col-span-2 border-l border-border pl-4 hidden md:block h-[calc(100vh-100px)] sticky top-20">
            <h3 className="text-[10px] font-bold uppercase text-muted-foreground mb-4 tracking-widest border-b border-border pb-2">Market Pulse</h3>
            
            <div className="mb-8">
                <h4 className="text-xs font-bold uppercase mb-3 flex items-center gap-2">
                    <ArrowUp className="w-3 h-3 text-emerald-500" /> 
                    Top Movers
                </h4>
                <div className="space-y-3">
                    {topMovers.length > 0 ? topMovers.map(c => (
                        <div key={c.id} className="text-xs border border-border p-3 rounded bg-card/50 cursor-pointer hover:border-primary transition-colors" onClick={() => navigate({ to: '/cards/$cardId', params: { cardId: String(c.id) } })}>
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold truncate w-20">{c.name}</span>
                                <span className="text-emerald-500 font-mono bg-emerald-900/20 px-1 rounded">+{c.price_delta_24h?.toFixed(1)}%</span>
                            </div>
                            <div className="text-[10px] text-muted-foreground uppercase truncate">{c.set_name}</div>
                        </div>
                    )) : <div className="text-xs text-muted-foreground italic">No active data yet.</div>}
                </div>
            </div>
            
            <div>
                <h4 className="text-xs font-bold uppercase mb-3 flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full border border-primary flex items-center justify-center">
                        <div className="w-1 h-1 bg-primary rounded-full"></div>
                    </div>
                    Volume Leaders
                </h4>
                <div className="space-y-3">
                    {topVolume.length > 0 ? topVolume.map((c, i) => (
                        <div key={c.id} className="text-xs border border-border p-3 rounded bg-card/50 cursor-pointer hover:border-primary transition-colors" onClick={() => navigate({ to: '/cards/$cardId', params: { cardId: String(c.id) } })}>
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold truncate w-20">{c.name}</span>
                                <span className="text-foreground font-mono">{c.volume_24h}</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-1 mt-2 overflow-hidden">
                                <div className="bg-primary h-full" style={{ width: `${Math.min(((c.volume_24h || 0) / (topVolume[0].volume_24h || 1)) * 100, 100)}%` }}></div>
                            </div>
                        </div>
                    )) : <div className="text-xs text-muted-foreground italic">No volume data yet.</div>}
                </div>
            </div>
        </div>
      </div>
    </div>
  )
}
