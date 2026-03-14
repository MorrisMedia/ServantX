import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

import { Link } from "wouter";

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center bg-white overflow-hidden pt-20 pb-32">
      <div className="container px-4 md:px-6 relative z-10 text-center max-w-4xl mx-auto">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="space-y-8"
        >
          <div className="inline-flex items-center rounded-full border border-border bg-secondary/50 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur-sm">
            <span className="flex h-1.5 w-1.5 rounded-full bg-chart-1 mr-2 animate-pulse"></span>
            Revenue Integrity Intelligence
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-[#0B2A4A] leading-[1.1]">
            Quietly correcting <br className="hidden md:block"/>
            hospital underpayments
          </h1>

          <p className="mx-auto max-w-2xl text-lg md:text-xl text-muted-foreground leading-relaxed">
            Revenue integrity technology from Servant Health that identifies and recovers underpaid claims using deterministic, contract-backed adjudication.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link 
              href="/request-pilot"
              className="w-full sm:w-auto inline-flex h-12 items-center justify-center rounded-md bg-servant-gradient px-8 text-base font-semibold text-white shadow-lg shadow-cyan-500/20 transition-all hover:scale-[1.02] hover:shadow-cyan-500/30"
            >
              Explore a Limited-Scope Pilot
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
          
          <p className="text-sm text-muted-foreground font-medium">
            No upfront cost. Contingency-based.
          </p>
        </motion.div>
      </div>

      {/* Subtle background decoration derived from the X */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] opacity-[0.03] pointer-events-none z-0">
         <svg viewBox="0 0 100 100" className="w-full h-full fill-[#0B2A4A]">
             <path d="M20 10 L45 50 L20 90 H35 L53 62 L71 90 H86 L61 50 L86 10 H71 L53 38 L35 10 Z" />
         </svg>
      </div>
    </section>
  );
}
