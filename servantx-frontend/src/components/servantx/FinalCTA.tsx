import { Link } from "wouter";
import { ArrowRight } from "lucide-react";

export function FinalCTA() {
  return (
    <section id="contact" className="py-24 bg-[#F6F8FB]">
      <div className="container px-4 md:px-6 max-w-3xl mx-auto text-center">
        <h2 className="text-4xl font-bold text-[#0B2A4A] mb-6">Start with a pilot</h2>
        <p className="text-xl text-muted-foreground mb-10">
          Focused. Measured. Contract-backed.
        </p>
        
        <div className="flex flex-col items-center gap-4">
          <Link
            href="/request-pilot"
            className="inline-flex h-14 items-center justify-center rounded-md bg-servant-gradient px-10 text-lg font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:scale-[1.02] hover:shadow-cyan-500/30"
          >
            Request a Pilot Review
            <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
          <span className="text-sm text-muted-foreground mt-4">
            No obligation. Confidential analysis.
          </span>
        </div>
      </div>
    </section>
  );
}
