import { FaqSection } from "@/components/marketing/FaqSection";
import { FeaturesSection } from "@/components/marketing/FeatureSection";
import Hero from "@/components/marketing/Hero";
import { LogoCarousel } from "@/components/marketing/LogoCarousel";
import { PricingSection } from "@/components/marketing/PricingSection";
import { TestimonialSection } from "@/components/marketing/TestimonialSection";
import { Navbar } from "@/components/marketing/Navbar";
import { Footer } from "@/components/marketing/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-white dark:bg-black">
        <div className="mx-auto max-w-7xl px-6 pt-40">
          <Hero />
          <LogoCarousel />
          <FeaturesSection />
          <TestimonialSection />
          <PricingSection />
          <FaqSection />
        </div>
      </main>
      <Footer />
    </>
  );
}
