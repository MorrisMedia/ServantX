import { Link } from "wouter";
import { Check } from "lucide-react";

export function Engagement() {
  return (
    <section className="py-24 bg-white">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="bg-[#0B2A4A] rounded-2xl p-8 md:p-12 text-white shadow-xl overflow-hidden relative">
          <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-6">Admin + analyst operating model</h2>
              <div className="space-y-4">
                {[
                  "Admin scope for tenant setup, contract libraries, and batch controls",
                  "Analyst scope for triage, validation, and appeal packet preparation",
                  "Visual reporting for CFO review and operational follow-through",
                  "Clear client and batch segmentation across up to 24 months of audits"
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-servant-gradient flex items-center justify-center shrink-0">
                      <Check className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className="font-medium text-white/90">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-xl p-8 backdrop-blur-sm space-y-4">
              <h3 className="text-xl font-semibold">What leaders need to see</h3>
              <p className="text-white/70 text-sm">
                Total underpayment exposure, top payer patterns, status by batch, and a clean path from finding to recovery packet.
              </p>
              <div className="grid gap-3 text-sm">
                <div className="rounded-lg border border-white/10 p-3">Executive summary by batch</div>
                <div className="rounded-lg border border-white/10 p-3">Finding detail with source-of-truth references</div>
                <div className="rounded-lg border border-white/10 p-3">Appeal draft package and next-action queue</div>
              </div>
              <Link href="/request-pilot" className="inline-block w-full py-3 px-6 rounded-md bg-white text-[#0B2A4A] font-bold hover:bg-gray-100 transition-colors text-center">
                Start Pilot Planning
              </Link>
            </div>
          </div>

          <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-servant-gradient opacity-20 blur-3xl rounded-full"></div>
        </div>
      </div>
    </section>
  );
}
