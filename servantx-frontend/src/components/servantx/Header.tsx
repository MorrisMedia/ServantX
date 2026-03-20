import { Link } from "wouter";

export function Logo() {
  return (
    <div className="flex items-center gap-2 font-sans select-none">
      <span className="text-2xl font-bold tracking-tight text-[#0B2A4A]">Servant</span>
      <div className="relative flex items-center justify-center w-8 h-8">
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-sm">
          <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#19C6C1" />
              <stop offset="50%" stopColor="#1FB3E6" />
              <stop offset="100%" stopColor="#1C7ED6" />
            </linearGradient>
          </defs>
          <path d="M25 15 L50 45 L75 15 H90 L60 50 L90 85 H75 L50 55 L25 85 H10 L40 50 L10 15 Z" fill="url(#logoGradient)" />
          <rect x="47" y="42" width="6" height="16" fill="white" rx="1" />
          <rect x="42" y="47" width="16" height="6" fill="white" rx="1" />
        </svg>
      </div>
    </div>
  );
}

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur-sm border-b border-border transition-all duration-200">
      <div className="container mx-auto px-4 md:px-6 h-20 flex items-center justify-between gap-4">
        <Link href="/" className="cursor-pointer hover:opacity-90 transition-opacity">
          <Logo />
        </Link>

        <nav className="hidden lg:flex items-center gap-8">
          <a href="#problem" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Why now</a>
          <a href="#focus" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Best-fit targets</a>
          <a href="#how-it-works" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Workflow</a>
          <a href="#governance" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">HIPAA & governance</a>
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/login" className="hidden sm:inline-flex h-10 items-center justify-center rounded-md border px-4 text-sm font-medium text-[#0B2A4A] hover:bg-accent">
            Login
          </Link>
          <Link
            href="/request-pilot"
            className="inline-flex h-10 items-center justify-center rounded-md bg-servant-gradient px-6 text-sm font-medium text-white shadow transition-all hover:opacity-90"
          >
            Request Pilot
          </Link>
        </div>
      </div>
    </header>
  );
}
