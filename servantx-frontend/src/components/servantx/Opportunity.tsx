export function Opportunity() {
  return (
    <section id="focus" className="py-24 bg-white">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-[#0B2A4A] tracking-tight mb-6">
            Best-fit targets first
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Start where payment logic is most defensible, public benchmarks exist, and operational recovery teams can move fast.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {[
            {
              title: "Ambulatory surgery centers",
              body: "High-volume, repeatable procedures with clear fee schedule logic and predictable payer behavior."
            },
            {
              title: "Orthopedic outpatient groups",
              body: "Strong fit for bundled logic review, modifier review, and repeat underpayment pattern detection."
            },
            {
              title: "In-network commercial claims",
              body: "Primary recovery target when contract terms are explicit and appeal posture is strongest."
            },
            {
              title: "Medicare + Medicaid",
              body: "Public source-of-truth schedules, locality data, and annual rate files support defensible audit baselines."
            }
          ].map((item) => (
            <div key={item.title} className="rounded-xl border bg-[#F6F8FB] p-6">
              <h3 className="text-lg font-semibold text-[#0B2A4A] mb-3">{item.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
