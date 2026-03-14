import { Header } from "@/components/servantx/Header";
import { Hero } from "@/components/servantx/Hero";
import { Problem } from "@/components/servantx/Problem";
import { Opportunity } from "@/components/servantx/Opportunity";
import { Solution } from "@/components/servantx/Solution";
import { FocusArea } from "@/components/servantx/FocusArea";
import { HowItWorks } from "@/components/servantx/HowItWorks";
import { Engagement } from "@/components/servantx/Engagement";
import { Trust } from "@/components/servantx/Trust";
import { Mission } from "@/components/servantx/Mission";
import { FinalCTA } from "@/components/servantx/FinalCTA";
import { Footer } from "@/components/servantx/Footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-background font-sans selection:bg-[#1FB3E6] selection:text-white">
      <Header />
      <main>
        <Hero />
        <Problem />
        <Opportunity />
        <Solution />
        <FocusArea />
        <HowItWorks />
        <Engagement />
        <Trust />
        <Mission />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
