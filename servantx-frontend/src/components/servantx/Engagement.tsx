import { Link } from "wouter";
import { Check } from "lucide-react";

export function Engagement() {
  return (
    <section className="py-24 bg-white">
      <div className="container px-4 md:px-6 max-w-4xl mx-auto">
        <div className="bg-[#0B2A4A] rounded-2xl p-8 md:p-12 text-white shadow-xl overflow-hidden relative">
          
          <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-6">Aligned incentives</h2>
              <div className="space-y-4">
                {[
                  "Contingency-based pricing",
                  "We only get paid if recovery occurs",
                  "No platform fees to start",
                  "Limited-scope pilot engagement"
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
            
            <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center backdrop-blur-sm">
              <h3 className="text-xl font-semibold mb-2">Pilot Program</h3>
              <p className="text-white/70 mb-6 text-sm">
                Experience the value with zero risk.
              </p>
              <Link
                href="/request-pilot"
                className="inline-block w-full py-3 px-6 rounded-md bg-white text-[#0B2A4A] font-bold hover:bg-gray-100 transition-colors"
              >
                Start Risk-Free
              </Link>
            </div>
          </div>

          {/* Background decoration */}
          <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-servant-gradient opacity-20 blur-3xl rounded-full"></div>
        </div>
      </div>
    </section>
  );
}
