export function FocusArea() {
  return (
    <section className="py-24 bg-white border-t border-border">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-[#0B2A4A] mb-4">What the platform needs to support</h2>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            The product is structured for multiple client organizations, repeat audit batches, deterministic adjudication, and executive-ready reporting.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            "Multiple clients with separate data boundaries",
            "Multiple audit batches per client across 24 months",
            "ZIP upload and batch normalization from billing exports",
            "Exportable findings, rationale, and appeal drafts",
          ].map((item) => (
            <div key={item} className="flex items-center justify-center rounded-lg border border-border bg-[#F6F8FB] p-5 text-center font-medium text-[#143A66]">
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
