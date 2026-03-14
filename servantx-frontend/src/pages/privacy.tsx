import { Link } from "wouter";
import { ChevronLeft } from "lucide-react";
import { Logo } from "@/components/servantx/Header";
import { Footer } from "@/components/servantx/Footer";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-[#F6F8FB] flex flex-col font-sans text-[#0B2A4A]">
      <header className="w-full bg-white border-b border-border py-4 sticky top-0 z-50">
        <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-muted-foreground hover:text-[#0B2A4A] transition-colors text-sm font-medium"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <div className="opacity-50 pointer-events-none grayscale">
            <Logo />
          </div>
        </div>
      </header>

      <main className="flex-1 py-16 px-4 md:px-6">
        <div className="max-w-3xl mx-auto">
          <div className="mb-12">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
              Privacy Policy
            </h1>
            <p className="text-muted-foreground">
              Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="bg-white rounded-lg border border-border p-8 md:p-10 shadow-sm space-y-6">
            <section>
              <h2 className="text-xl font-semibold mb-4">Introduction</h2>
              <p className="text-muted-foreground leading-relaxed">
                ServantX ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website or use our services.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Information We Collect</h2>
              <p className="text-muted-foreground leading-relaxed mb-3">
                We may collect information that you provide directly to us, including:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                <li>Contact information (name, email address, phone number)</li>
                <li>Organization information (hospital name, state/region)</li>
                <li>Professional information (title, role)</li>
                <li>Any other information you choose to provide through our forms or communications</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">How We Use Your Information</h2>
              <p className="text-muted-foreground leading-relaxed mb-3">
                We use the information we collect to:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                <li>Respond to your inquiries and requests</li>
                <li>Provide, maintain, and improve our services</li>
                <li>Communicate with you about our services</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Information Sharing</h2>
              <p className="text-muted-foreground leading-relaxed">
                We do not sell, trade, or rent your personal information to third parties. We may share your information only in the following circumstances:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4 mt-3">
                <li>With your consent</li>
                <li>To comply with legal obligations</li>
                <li>To protect our rights and safety</li>
                <li>With service providers who assist us in operating our business</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Data Security</h2>
              <p className="text-muted-foreground leading-relaxed">
                We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Contact Us</h2>
              <p className="text-muted-foreground leading-relaxed">
                If you have questions about this Privacy Policy, please contact us through our{" "}
                <Link href="/request-pilot" className="text-[#143A66] font-medium hover:underline">
                  contact form
                </Link>
                .
              </p>
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

