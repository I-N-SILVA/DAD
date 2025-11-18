"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Wand2,
  Calendar,
  BarChart3,
  Users,
  Image as ImageIcon,
  Database,
  TrendingUp,
  MessageSquare,
  FileText,
  X
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface SidebarProps {
  open?: boolean
  onClose?: () => void
}

const navigation = [
  {
    title: "Overview",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
      { name: "Analytics", href: "/analytics", icon: BarChart3, badge: "New" },
    ],
  },
  {
    title: "Content",
    items: [
      { name: "Generate", href: "/generate", icon: Wand2 },
      { name: "Queue", href: "/queue", icon: Calendar, badge: 5 },
      { name: "Knowledge Base", href: "/knowledge", icon: Database },
      { name: "Visual Content", href: "/visual", icon: ImageIcon },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { name: "Trends", href: "/trends", icon: TrendingUp },
      { name: "Competitors", href: "/competitors", icon: Users },
      { name: "Engagement", href: "/engagement", icon: MessageSquare },
    ],
  },
  {
    title: "Management",
    items: [
      { name: "Posted Tweets", href: "/tweets", icon: FileText },
    ],
  },
]

export function Sidebar({ open = true, onClose }: SidebarProps) {
  const pathname = usePathname()

  return (
    <>
      {/* Overlay for mobile */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 h-full w-64 border-r bg-background transition-transform duration-300 ease-in-out md:sticky md:top-16 md:h-[calc(100vh-4rem)] md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Mobile header */}
          <div className="flex h-16 items-center justify-between border-b px-4 md:hidden">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <span className="text-lg font-bold">X</span>
              </div>
              <span className="font-bold">Content RAG</span>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            <div className="space-y-6">
              {navigation.map((section, index) => (
                <div key={section.title}>
                  {index > 0 && <Separator className="my-4" />}
                  <div className="space-y-1">
                    <h4 className="mb-2 px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {section.title}
                    </h4>
                    {section.items.map((item) => {
                      const isActive = pathname === item.href
                      return (
                        <Link
                          key={item.name}
                          href={item.href}
                          onClick={() => {
                            // Close sidebar on mobile when navigating
                            if (window.innerWidth < 768) {
                              onClose?.()
                            }
                          }}
                          className={cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent",
                            isActive
                              ? "bg-accent text-accent-foreground"
                              : "text-muted-foreground hover:text-foreground"
                          )}
                        >
                          <item.icon className="h-4 w-4" />
                          <span className="flex-1">{item.name}</span>
                          {item.badge && (
                            <Badge variant={typeof item.badge === 'string' ? 'secondary' : 'default'} className="h-5 px-1.5">
                              {item.badge}
                            </Badge>
                          )}
                        </Link>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </nav>

          {/* Footer */}
          <div className="border-t p-4">
            <div className="rounded-lg bg-muted p-3">
              <p className="text-xs font-medium">System Status</p>
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="success" dot className="text-xs">
                  All Systems Operational
                </Badge>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Last sync: Just now
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
