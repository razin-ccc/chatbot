import {
  BotIcon,
  FileTextIcon,
  HistoryIcon,
  PlusIcon,
  SearchCheckIcon,
  ServerIcon,
  BookOpenIcon,
} from "lucide-react";

import * as AccordionPrimitive from "@radix-ui/react-accordion";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
} from "@/components/ui/accordion";

export function FaqSection() {
  const items = [
    {
      icon: BotIcon,
      title: "What is Chat?",
      content:
        "Chat is a full-stack AI chat application with user authentication, persistent conversations, Gemini streaming responses, and optional document-grounded answers.",
    },
    {
      icon: FileTextIcon,
      title: "How does document chat work?",
      content:
        "Upload a PDF or TXT file inside a conversation. After it is indexed, document mode retrieves relevant chunks from that conversation's documents and streams a grounded Gemini answer.",
    },
    {
      icon: BookOpenIcon,
      title: "Can I switch back to normal chat?",
      content:
        "Yes. The document-mode toggle lets you use normal Gemini chat even when indexed documents are attached to the current conversation.",
    },
    {
      icon: SearchCheckIcon,
      title: "Are documents shared across conversations?",
      content:
        "No. Documents are scoped to the conversation where they were uploaded, so files in one chat do not affect answers in another chat.",
    },
    {
      icon: HistoryIcon,
      title: "Is conversation history saved?",
      content:
        "Yes. Conversations and messages are stored in PostgreSQL, and the chat page lets you reopen previous threads from the sidebar.",
    },
    {
      icon: ServerIcon,
      title: "What powers the backend?",
      content:
        "The backend uses FastAPI, PostgreSQL, Redis, Chroma, BGE embeddings, and Google Gemini. Assistant replies are streamed to the frontend over Server-Sent Events.",
    },
  ];

  return (
    <div id="faq" className="py-24 sm:py-32">
      <div className="text-center mb-16">
        <h2 className="text-4xl md:text-5xl font-bold mb-4 text-neutral-800 dark:text-neutral-100">
          Frequently Asked Questions
        </h2>
        <p className="text-lg md:text-xl text-neutral-600 dark:text-neutral-400 max-w-3xl mx-auto">
          Practical details about authentication, streaming chat, document
          uploads, and how ChatDeck routes document-grounded answers.
        </p>
      </div>
      <Accordion
        type="single"
        collapsible
        className="max-w-4xl mx-auto"
        defaultValue="item-1"
      >
        {items.map((item, index) => (
          <AccordionItem key={index} value={`item-${index + 1}`}>
            <AccordionPrimitive.Header className="flex">
              <AccordionPrimitive.Trigger
                data-slot="accordion-trigger"
                className="focus-visible:border-ring focus-visible:ring-ring/50 flex flex-1 items-start justify-between gap-4 rounded-md py-4 text-left text-sm font-medium transition-all outline-none focus-visible:ring-[3px] disabled:pointer-events-none disabled:opacity-50 [&[data-state=open]>svg]:rotate-45"
              >
                <span className="flex items-center gap-4">
                  <item.icon className="size-4 shrink-0" />
                  <span>{item.title}</span>
                </span>
                <PlusIcon className="text-muted-foreground pointer-events-none size-4 shrink-0 transition-transform duration-200" />
              </AccordionPrimitive.Trigger>
            </AccordionPrimitive.Header>
            <AccordionContent className="text-muted-foreground">
              {item.content}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
