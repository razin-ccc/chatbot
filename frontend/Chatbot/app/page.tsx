import { FaqSection } from "@/components/Blocks/FaqSection";
import { FeaturesSection } from "@/components/Blocks/FeatureSection";
import Hero from "@/components/Blocks/Hero";
import { LogoCarousel } from "@/components/Blocks/LogoCarousel";
import { PricingSection } from "@/components/Blocks/PricingSection";
import { TeamSection } from "@/components/Blocks/TeamSection";
import { TestimonialSection } from "@/components/Blocks/TestimonialSection";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/Blocks/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-white dark:bg-black">
        <div className="mx-auto max-w-7xl px-6 pt-40">
          <Hero />
          <LogoCarousel />
          <FeaturesSection />
          <TeamSection />
          <TestimonialSection />
          <PricingSection />
          <FaqSection />
        </div>
      </main>
      <Footer />
    </>
  );
}
