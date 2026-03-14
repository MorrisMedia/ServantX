import { Lock, FileText, Scale, User, Shield } from "lucide-react";

export function Trust() {
  return (
    <section id="governance" className="py-24 bg-[#F6F8FB]">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-[#0B2A4A] mb-4">Built for CFOs and compliance</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Governance, transparency, and auditability are at the core of our architecture.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: FileText,
              title: "Fully auditable calculations",
              text: "Every identified underpayment is backed by a transparent logic trail."
            },
            {
              icon: Scale,
              title: "Contract & citation transparency",
              text: "We reference the specific contract terms and payer policies violated."
            },
            {
              icon: Shield,
              title: "No medical necessity arguments",
              text: "We focus purely on administrative and contractual underpayments."
            },
            {
              icon: Lock,
              title: "No Medicare RAC exposure",
              text: "Our methods are compliant and do not create take-back risks."
            },
            {
              icon: User,
              title: "Human oversight built in",
              text: "Expert review before any claim is flagged for recovery."
            }
          ].map((item, i) => (
            <div key={i} className="bg-white p-8 rounded-lg border border-border shadow-sm hover:shadow-md transition-shadow">
              <item.icon className="w-10 h-10 text-[#143A66] mb-4" />
              <h3 className="text-lg font-bold text-[#0B2A4A] mb-2">{item.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
