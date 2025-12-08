import { Link } from '@tanstack/react-router'
import { Lock } from 'lucide-react'
import { DiscordIcon } from './icons/DiscordIcon'

type LoginUpsellOverlayProps = {
  title?: string
  description?: string
  className?: string
}

/**
 * Blurred overlay with login CTA for gated features.
 * Use as a sibling overlay on top of the content to blur.
 */
export function LoginUpsellOverlay({
  title = "Unlock Full Access",
  description = "Sign in to access premium features and detailed market analytics.",
  className = ""
}: LoginUpsellOverlayProps) {
  return (
    <div className={`absolute inset-0 z-20 flex items-center justify-center ${className}`}>
      {/* Blur backdrop */}
      <div className="absolute inset-0 backdrop-blur-[2px] bg-background/40" />

      {/* CTA Card */}
      <div className="relative z-10 bg-card border border-border rounded-lg p-6 max-w-sm mx-4 text-center shadow-xl">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Lock className="w-6 h-6 text-primary" />
        </div>
        <h3 className="text-lg font-bold uppercase tracking-tight mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
        <div className="flex flex-col gap-2">
          <Link
            to="/login"
            className="w-full px-4 py-2.5 bg-[#5865F2] text-white rounded font-bold uppercase text-xs hover:bg-[#4752C4] transition-colors flex items-center justify-center gap-2"
          >
            <DiscordIcon className="w-4 h-4" />
            Sign in with Discord
          </Link>
          <Link
            to="/login"
            className="w-full px-4 py-2.5 border border-border text-foreground rounded font-bold uppercase text-xs hover:bg-muted transition-colors"
          >
            Sign in with Email
          </Link>
        </div>
        <p className="text-[10px] text-muted-foreground mt-3">Free account • No credit card required</p>
      </div>
    </div>
  )
}

/**
 * Compact inline button for smaller gated sections.
 * Shows Discord-styled sign-in button with blur backdrop.
 */
export function LoginUpsellButton({ title = "Sign in to view" }: { title?: string }) {
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center backdrop-blur-[2px] bg-background/40 rounded">
      <Link
        to="/login"
        className="flex items-center gap-2 px-3 py-1.5 bg-[#5865F2] text-white rounded font-bold uppercase text-[10px] hover:bg-[#4752C4] transition-colors"
      >
        <DiscordIcon className="w-3.5 h-3.5" />
        {title}
      </Link>
    </div>
  )
}
