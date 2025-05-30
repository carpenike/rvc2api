import { AccentSelect } from "@/components/accent-select";
import { NavLinks, SidebarBrand, UserFooter } from "@/components/side-nav";
import { ThemeToggle } from "@/components/theme-toggle";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

import { Menu } from "lucide-react";

export function MainNav() {
  return (
    <header className="flex h-14 items-center gap-4 border-b px-4">
      {/* ── mobile hamburger │ visible < md ─────────────────────── */}
      <Sheet>
        <SheetTrigger className="md:hidden">
          <Menu className="h-5 w-5" />
        </SheetTrigger>
        <SheetContent side="left" className="flex w-56 flex-col p-0">
          <SidebarBrand />   {/* ← brand inside sheet */}
          <NavLinks />
          <UserFooter />
        </SheetContent>

        {/* mobile sidebar sheet (re-uses NavLinks & UserFooter) */}
        <SheetContent side="left" className="flex w-56 flex-col p-0">
          <NavLinks />
          <UserFooter />
        </SheetContent>
      </Sheet>

      {/* brand / logo */}
      <span className="text-lg font-semibold">My App</span>

      {/* desktop nav menu */}
      <NavigationMenu className="hidden sm:flex">
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink href="/">Home</NavigationMenuLink>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuLink href="/settings">Settings</NavigationMenuLink>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>

      {/* right-side actions */}
      <div className="ml-auto flex items-center gap-2">
        <AccentSelect />   {/* accent + light/dark elsewhere */}
        <ThemeToggle />
      </div>
    </header>
  );
}
