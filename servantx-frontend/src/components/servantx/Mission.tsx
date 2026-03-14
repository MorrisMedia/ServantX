export function Mission() {
  return (
    <section className="py-24 bg-white border-t border-border">
      <div className="container px-4 md:px-6 max-w-3xl mx-auto text-center">
        <h2 className="text-3xl font-bold text-[#0B2A4A] mb-8">Mission-driven and veteran-led</h2>
        
        <p className="text-lg text-muted-foreground leading-relaxed mb-12">
          ServantX is a Disabled Veteran Owned Business, built with a commitment to stewardship, accountability, and service. Our work reflects the same principles we bring to hospital partnerships:
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {["Integrity", "Discipline", "Responsibility", "Respect"].map((val, i) => (
            <div key={i} className="p-4 bg-[#F6F8FB] rounded-lg text-[#143A66] font-semibold">
              {val}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
