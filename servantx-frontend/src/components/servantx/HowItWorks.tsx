import { Database, FileCode, CheckSquare, Upload, ArrowRight } from "lucide-react";

export function HowItWorks() {
  const steps = [
    { title: "Ingest paid claims", icon: Upload },
    { title: "Normalize payment data", icon: Database },
    { title: "Apply deterministic reimbursement logic", icon: FileCode },
    { title: "Identify underpayments", icon: SearchIcon }, // Defining below
    { title: "Generate appeal packets", icon: FileCheckIcon },
    { title: "Human approval before submission", icon: UserCheckIcon }
  ];

  return (
    <section id="how-it-works" className="py-24 bg-[#F6F8FB]">
      <div className="container px-4 md:px-6 max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold text-[#0B2A4A] text-center mb-16">How it works</h2>

        <div className="relative">
          {/* Connecting line for desktop */}
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
            No billing workflow disruption. No system replacement.
          </p>
        </div>
      </div>
    </section>
  );
}

// Helper icons
function SearchIcon(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> }
function FileCheckIcon(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg> }
function UserCheckIcon(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg> }
