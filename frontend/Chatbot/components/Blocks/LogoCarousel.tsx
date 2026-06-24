"use client";

import { Card } from "@/components/ui/card";
import {
  BrainCircuit,
  DatabaseZap,
  DatabaseZapIcon,
  Radio,
  ShieldCheck,
} from "lucide-react";
import type { IconType } from "react-icons";
import {
  SiFastapi,
  SiGooglegemini,
  SiNextdotjs,
  SiPostgresql,
  SiReact,
  SiRedis,
  SiTailwindcss,
  SiTypescript,
} from "react-icons/si";

const techStack: { name: string; icon: IconType }[] = [
  { name: "Next.js", icon: SiNextdotjs },
  { name: "React", icon: SiReact },
  { name: "FastAPI", icon: SiFastapi },
  { name: "PostgreSQL", icon: SiPostgresql },
  { name: "Redis", icon: SiRedis },
  { name: "Pinecone", icon: DatabaseZap },
  { name: "Gemini", icon: SiGooglegemini },
  { name: "SSE Streaming", icon: Radio },
  { name: "Tailwind CSS", icon: SiTailwindcss },
  { name: "JWT Auth", icon: ShieldCheck },
  { name: "BGE Embeddings", icon: BrainCircuit },
  { name: "TypeScript", icon: SiTypescript },
] as const;

export function LogoCarousel() {
  return (
    <section className="pb-12 sm:pb-16 lg:pb-20 pt-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="font-medium text-muted-foreground mb-8">
            Powered by the tools behind real-time document-aware chat
          </p>

          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-20 bg-linear-to-r from-background to-transparent z-10 pointer-events-none" />
            <div className="absolute right-0 top-0 bottom-0 w-20 bg-linear-to-l from-background to-transparent z-10 pointer-events-none" />

            <div className="overflow-hidden">
              <div className="flex animate-logo-scroll space-x-8 sm:space-x-12">
                {techStack.map((item, index) => (
                  <TechStackCard key={`first-${index}`} {...item} />
                ))}
                {techStack.map((item, index) => (
                  <TechStackCard key={`second-${index}`} {...item} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TechStackCard({ name, icon: Icon }: { name: string; icon: IconType }) {
  return (
    <Card className="shrink-0 flex items-center justify-center h-16 w-40 opacity-60 hover:opacity-100 transition-opacity duration-300 border-0 shadow-none bg-transparent">
      <div className="flex items-center gap-3">
        <Icon className="size-6 text-foreground" />
        <span className="text-foreground text-base font-semibold whitespace-nowrap">
          {name}
        </span>
      </div>
    </Card>
  );
}
