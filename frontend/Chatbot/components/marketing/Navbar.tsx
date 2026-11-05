"use client";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { Menu } from "lucide-react";
import Link from "next/link";
import React from "react";

const menuItems = [
  { name: "Features", href: "#features" },
  { name: "Testimonials", href: "#testimonials" },
  { name: "Pricing", href: "#pricing" },
  { name: "FAQ", href: "#faq" },
];

export const Navbar = () => {
  const [menuOpen, setMenuOpen] = React.useState(false);
  const [isScrolled, setIsScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const closeMenu = () => setMenuOpen(false);

  return (
    <nav className="fixed z-20 w-full px-2">
      <div
        className={cn(
          "mx-auto mt-2 max-w-6xl px-6 transition-[max-width,background-color,padding] duration-300 lg:px-12",
          isScrolled &&
            "bg-background/50 max-w-4xl rounded-full border backdrop-blur-lg lg:px-6",
        )}
      >
        <div className="relative flex items-center justify-between py-2 lg:py-2.5">
          <Link
            href="/"
            aria-label="home"
            className="flex items-center space-x-2"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary dark:bg-primary/30">
              <svg
                className="h-6 w-6 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              Chat
            </span>
          </Link>

          <div className="absolute inset-0 m-auto hidden size-fit lg:block">
            <ul className="flex gap-8 text-sm">
              {menuItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-muted-foreground hover:text-accent-foreground text-base block duration-150"
                  >
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="hidden items-center gap-3 lg:flex">
            <AnimatedThemeToggler />
            <Button asChild variant="ghost" size="sm" className="rounded-full">
              <Link href="/login">
                <span>Login</span>
              </Link>
            </Button>
            <Button asChild size="sm" className="rounded-full">
              <Link href="/register">
                <span>Get Started</span>
              </Link>
            </Button>
          </div>

          {/* The menu is portaled out of the pill above, so opening it can't resize the pill. */}
          <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Open menu"
                className="lg:hidden"
              >
                <Menu className="size-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 sm:max-w-xs">
              <SheetHeader>
                <SheetTitle>Menu</SheetTitle>
                <SheetDescription className="sr-only">
                  Site navigation
                </SheetDescription>
              </SheetHeader>
              <div className="flex flex-col gap-8 px-4 pb-6">
                <ul className="space-y-6 text-base">
                  {menuItems.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={closeMenu}
                        className="text-muted-foreground hover:text-accent-foreground block duration-150"
                      >
                        <span>{item.name}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
                <div className="flex flex-col gap-3">
                  <AnimatedThemeToggler />
                  <Button asChild variant="ghost" size="sm" className="rounded-full">
                    <Link href="/login" onClick={closeMenu}>
                      <span>Login</span>
                    </Link>
                  </Button>
                  <Button asChild size="sm" className="rounded-full">
                    <Link href="/register" onClick={closeMenu}>
                      <span>Get Started</span>
                    </Link>
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  );
};
