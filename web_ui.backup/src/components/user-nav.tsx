import { useSidebar } from "@/hooks/useSidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, Settings, User } from "lucide-react";

type UserInfo = {
  name: string;
  email: string;
  avatarUrl?: string;
};

const currentUser: UserInfo = {
  name: "Ada Lovelace",
  email: "ada@byte.com",
  avatarUrl: "https://i.pravatar.cc/150?img=47",
};

export function UserNav() {
  const { collapsed } = useSidebar();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div
          className={`flex cursor-pointer items-center gap-3 rounded-md p-3 hover:bg-muted/50 ${
            collapsed ? "justify-center" : "w-full"
          }`}
        >
          <Avatar className="h-8 w-8">
            <AvatarImage src={currentUser.avatarUrl} />
            <AvatarFallback>{currentUser.name[0]}</AvatarFallback>
          </Avatar>

          {/* Hide text when sidebar is collapsed */}
          {!collapsed && (
            <div className="flex flex-col text-left">
              <span className="text-sm font-medium leading-none">
                {currentUser.name}
              </span>
              <span className="text-xs text-muted-foreground">
                {currentUser.email}
              </span>
            </div>
          )}
        </div>
      </DropdownMenuTrigger>

      {/* Dropdown always shows full info */}
      <DropdownMenuContent side="top" align="start" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{currentUser.name}</p>
            <p className="text-xs text-muted-foreground">{currentUser.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
