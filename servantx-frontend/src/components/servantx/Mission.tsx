export function Mission() {
  return (
    <section className="py-24 bg-white border-t border-border">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-[#0B2A4A] mb-4">Background audit protection plan</h2>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            The long-term agent layer should protect operations, not replace adjudication. It should watch batches, flag exceptions for admins,
            and summarize non-PHI operational signals in the background.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-xl border bg-[#F6F8FB] p-6">
            <h3 className="font-semibold text-[#0B2A4A] mb-3">Allowed agent tasks</h3>
            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-5">
              <li>Monitor batch completion, failures, and queue delays</li>
              <li>Summarize counts, patterns, and non-PHI variance metrics</li>
              <li>Prepare admin review queues and escalation alerts</li>
              <li>Draft structured narratives from already-approved findings</li>
            </ul>
          </div>
          <div className="rounded-xl border bg-[#F6F8FB] p-6">
            <h3 className="font-semibold text-[#0B2A4A] mb-3">Prohibited agent tasks</h3>
            <ul className="space-y-2 text-sm text-muted-foreground list-disc pl-5">
              <li>No raw PHI to external models</li>
              <li>No unsupervised payment decisions or appeal submission</li>
              <li>No unsupported reimbursement conclusions without citations</li>
              <li>No tenant-crossing access across client environments</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
