import { ShieldCheck, Calculator, FileCheck, Search } from "lucide-react";

export function Solution() {
  return (
    <section id="solution" className="py-24 bg-[#0B2A4A] text-white">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-4">
            Deterministic revenue integrity
          </h2>
          <div className="w-16 h-1 bg-white/20 rounded-full mx-auto"></div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              icon: Search,
              title: "Audits paid claims (835 ERA)",
              desc: "Comprehensive review of every line item against expected reimbursement."
            },
            {
              icon: Calculator,
              title: "Applies contract and OPPS/APC logic",
              desc: "Precise recalculation based on your specific payer agreements."
            },
            {
              icon: FileCheck,
              title: "Calculates expected vs paid amounts",
              desc: "Identify variances down to the penny with mathematical certainty."
            },
            {
              icon: ShieldCheck,
              title: "Flags high-confidence underpayments",
              desc: "Produces appeal-ready recovery packets for your team."
            }
          ].map((item, i) => (
            <div key={i} className="flex gap-5 p-6 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors">
              <div className="shrink-0 w-12 h-12 rounded-full bg-servant-gradient flex items-center justify-center text-white">
                <item.icon className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-white/70">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="inline-block px-4 py-2 rounded-full bg-white/10 text-sm font-medium text-white/80 border border-white/20">
            AI assists with extraction and explanation — never with dollar decisions.
          </p>
        </div>
      </div>
    </section>
  );
}
