export function FocusArea() {
  return (
    <section className="py-24 bg-white">
      <div className="container px-4 md:px-6 max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-[#0B2A4A] mb-4">Where we start</h2>
          <p className="text-lg text-muted-foreground">
            Outpatient facility claims where payment logic is rules-based and appeal success is highest.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            "Modifier -25",
            "Modifier -59",
            "Modifier -XE",
            "Modifier -XP",
            "Modifier -XS",
            "Modifier -XU"
          ].map((mod, i) => (
            <div 
              key={i} 
              className={`
                flex items-center justify-center p-4 rounded-lg border border-border bg-[#F6F8FB]
                text-[#143A66] font-semibold text-center transition-all hover:border-[#19C6C1] hover:shadow-sm
                ${i >= 2 ? "col-span-1 md:col-span-1" : "col-span-1 md:col-span-2"}
              `}
            >
              {mod}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
