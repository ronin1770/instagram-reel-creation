"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavigationItem = {
  href: string;
  label: string;
  matchesPath?: (pathname: string) => boolean;
};

const navigationItems: NavigationItem[] = [
  {
    href: "/",
    label: "Home",
    matchesPath: (pathname) => pathname === "/",
  },
  {
    href: "/videos",
    label: "Videos",
    matchesPath: (pathname) => pathname === "/videos" || pathname.startsWith("/videos/"),
  },
  {
    href: "/create_video",
    label: "Create Video",
    matchesPath: (pathname) =>
      pathname === "/create_video" || pathname.startsWith("/create_video/"),
  },
  {
    href: "#",
    label: "Post Wizard",
  },
  {
    href: "/control-panel",
    label: "Settings",
    matchesPath: (pathname) =>
      pathname === "/control-panel" || pathname.startsWith("/control-panel/"),
  },
];

export default function AppNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary navigation" className="app-nav">
      {navigationItems.map(({ href, label, matchesPath }) => {
        const isActive = matchesPath?.(pathname) ?? false;

        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={`app-nav__link${isActive ? " app-nav__link--active" : ""}`}
            href={href}
            key={label}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
