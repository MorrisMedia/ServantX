import { motion } from "framer-motion";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export function Problem() {
  return (
    <section id="problem" className="py-24 bg-[#F6F8FB]">
      <div className="container px-4 md:px-6 max-w-5xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div className="space-y-6">
            <h2 className="text-3xl md:text-4xl font-bold text-[#0B2A4A] tracking-tight">
              Hospitals are systematically underpaid
            </h2>
            <div className="w-16 h-1 bg-servant-gradient rounded-full"></div>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Most of this revenue is never pursued — not because it isn’t owed, but because it’s difficult to identify at scale.
            </p>
          </div>

          <div className="space-y-4">
            {[
              "Payer contracts are misapplied at scale",
              "Modifiers are ignored",
              "Bundling rules are misused",
              "Small underpayments go unchallenged"
            ].map((item, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-4 p-4 bg-white rounded-lg border border-border shadow-sm"
              >
                <AlertCircle className="w-6 h-6 text-chart-3 shrink-0 mt-0.5" />
                <span className="text-[#0B2A4A] font-medium text-lg">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
