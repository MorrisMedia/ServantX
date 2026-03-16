import { Database, FileCode, CheckSquare, Upload, BarChart3, ShieldCheck } from "lucide-react";

export function HowItWorks() {
  const steps = [
    { title: "Upload batch exports from the billing system", icon: Upload },
    { title: "Normalize files into audit-ready batch records", icon: Database },
    { title: "Apply deterministic contract and public-rate logic", icon: FileCode },
    { title: "Flag only high-confidence underpayments", icon: CheckSquare },
    { title: "Generate analyst views and visual reports", icon: BarChart3 },
    { title: "Prepare appeal-ready evidence with admin approval", icon: ShieldCheck },
  ];

  return (
    <section id="how-it-works" className="py-24 bg-[#F6F8FB]">
      <div className="container px-4 md:px-6 max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-[#0B2A4A] text-center mb-16">Operational workflow</h2>

        <div className="relative">
          <div className="hidden md:block absolute top-12 left-0 right-0 h-0.5 bg-gray-200 -z-10" />
          <div className="grid grid-cols-1 md:grid-cols-6 gap-8">
            {steps.map((step, i) => (
              <div key={i} className="flex flex-col items-center text-center group">
                <div className="w-24 h-24 rounded-full bg-white border-4 border-[#F6F8FB] shadow-sm flex items-center justify-center mb-6 group-hover:border-[#1FB3E6] transition-colors relative z-10">
                  <step.icon className="w-8 h-8 text-[#143A66]" />
                  <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-[#1FB3E6] text-white flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-[#0B2A4A] px-2">{step.title}</h3>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 text-center pt-8 border-t border-gray-200">
          <p className="text-muted-foreground font-medium">
            No LLM is allowed to decide payment correctness. AI is constrained to support workflows that do not require PHI disclosure.
          </p>
        </div>
      </div>
    </section>
  );
}
