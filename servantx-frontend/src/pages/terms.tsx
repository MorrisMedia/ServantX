import { Link } from "wouter";
import { ChevronLeft } from "lucide-react";
import { Logo } from "@/components/servantx/Header";
import { Footer } from "@/components/servantx/Footer";

export default function Terms() {
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
              Terms of Service
            </h1>
            <p className="text-muted-foreground">
              Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="bg-white rounded-lg border border-border p-8 md:p-10 shadow-sm space-y-6">
            <section>
              <h2 className="text-xl font-semibold mb-4">Agreement to Terms</h2>
              <p className="text-muted-foreground leading-relaxed">
                By accessing or using ServantX's website and services, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Use of Services</h2>
              <p className="text-muted-foreground leading-relaxed mb-3">
                You agree to use our services only for lawful purposes and in accordance with these Terms. You agree not to:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                <li>Violate any applicable laws or regulations</li>
                <li>Infringe upon the rights of others</li>
                <li>Transmit any harmful or malicious code</li>
                <li>Attempt to gain unauthorized access to our systems</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Pilot Program</h2>
              <p className="text-muted-foreground leading-relaxed">
                Participation in our pilot program is subject to separate agreements and terms. All pilot reviews are exploratory and do not obligate participation. Findings are contract-backed and require your approval before any submission.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Intellectual Property</h2>
              <p className="text-muted-foreground leading-relaxed">
                All content, features, and functionality of our services, including but not limited to text, graphics, logos, and software, are owned by ServantX and are protected by copyright, trademark, and other intellectual property laws.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Disclaimer of Warranties</h2>
              <p className="text-muted-foreground leading-relaxed">
                Our services are provided "as is" and "as available" without warranties of any kind, either express or implied. We do not guarantee that our services will be uninterrupted, secure, or error-free.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Limitation of Liability</h2>
              <p className="text-muted-foreground leading-relaxed">
                To the maximum extent permitted by law, ServantX shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of our services.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Changes to Terms</h2>
              <p className="text-muted-foreground leading-relaxed">
                We reserve the right to modify these Terms of Service at any time. We will notify you of any material changes by posting the new terms on this page and updating the "Last updated" date.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4">Contact Us</h2>
              <p className="text-muted-foreground leading-relaxed">
                If you have questions about these Terms of Service, please contact us through our{" "}
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

