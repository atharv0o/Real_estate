"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme, theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isDark = mounted ? resolvedTheme === "dark" : true;

  return (
    <div className="flex items-center rounded-full border border-border bg-background/60 p-1 shadow-glass backdrop-blur-xl">
      <Button
        type="button"
        variant={isDark ? "secondary" : "ghost"}
        size="icon"
        aria-label="Use dark theme"
        onClick={() => setTheme("dark")}
        className="h-8 w-8"
      >
        <Moon className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant={!isDark && theme !== "system" ? "secondary" : "ghost"}
        size="icon"
        aria-label="Use light theme"
        onClick={() => setTheme("light")}
        className="h-8 w-8"
      >
        <Sun className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant={theme === "system" ? "secondary" : "ghost"}
        size="icon"
        aria-label="Use system theme"
        onClick={() => setTheme("system")}
        className="h-8 w-8"
      >
        <Monitor className="h-4 w-4" />
      </Button>
    </div>
  );
}
