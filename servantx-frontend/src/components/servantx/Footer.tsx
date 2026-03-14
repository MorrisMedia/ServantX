import { Link } from "wouter";

export function Footer() {
  return (
    <footer className="bg-[#0B2A4A] text-white/60 py-12 text-sm border-t border-white/10">
      <div className="container px-4 md:px-6 mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex flex-col gap-1">
          <span className="font-semibold text-white">ServantX</span>
          <span>A Servant Health company</span>
          <span>Disabled Veteran Owned Business</span>
        </div>
        
        <div className="flex gap-8">
          <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
          <Link href="/terms" className="hover:text-white transition-colors">Terms</Link>
          <Link href="/contact" className="hover:text-white transition-colors">Contact</Link>
        </div>
        
        <div className="text-right">
          &copy; {new Date().getFullYear()} ServantX. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
