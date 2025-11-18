"use client"

import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  TrendingUp,
  Calendar,
  MessageSquare,
  BarChart3,
  Zap,
  ArrowUpRight,
  Clock,
  Check
} from "lucide-react"
import { formatNumber, formatPercentage } from "@/lib/utils"

export default function DashboardPage() {
  // Mock data - will be replaced with API calls
  const stats = {
    totalTweets: 156,
    avgEngagement: 0.072,
    queuedTweets: 8,
    activeTrends: 3,
  }

  const recentActivity = [
    {
      id: 1,
      type: "tweet",
      content: "Just published a new tweet about AI trends",
      time: "2 hours ago",
      status: "success",
    },
    {
      id: 2,
      type: "queue",
      content: "5 tweets auto-scheduled for optimal timing",
      time: "3 hours ago",
      status: "info",
    },
    {
      id: 3,
      type: "trend",
      content: "New trend detected: #AIRevolution",
      time: "4 hours ago",
      status: "warning",
    },
  ]

  const topPerformers = [
    {
      id: 1,
      content: "AI is transforming how we create content. Here's what you need to know... 🧵",
      engagement: 0.095,
      likes: 245,
      retweets: 89,
    },
    {
      id: 2,
      content: "The future of content creation is here. Machine learning + RAG = 🚀",
      engagement: 0.087,
      likes: 198,
      retweets: 67,
    },
    {
      id: 3,
      content: "Quick tip: Use analytics to understand what resonates with your audience",
      engagement: 0.076,
      likes: 156,
      retweets: 45,
    },
  ]

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome back! Here's what's happening with your content.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tweets</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.totalTweets)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-success inline-flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +12% from last month
              </span>
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Engagement</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(stats.avgEngagement)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-success inline-flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +0.8% from last week
              </span>
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Queued Tweets</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.queuedTweets}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Ready for publishing
            </p>
            <Button variant="link" className="px-0 mt-2 h-auto text-xs" asChild>
              <a href="/queue">
                View queue <ArrowUpRight className="h-3 w-3 ml-1" />
              </a>
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Trends</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeTrends}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Trending in your niche
            </p>
            <Button variant="link" className="px-0 mt-2 h-auto text-xs" asChild>
              <a href="/trends">
                Explore trends <ArrowUpRight className="h-3 w-3 ml-1" />
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Latest updates from your content system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={activity.id}>
                  {index > 0 && <Separator className="my-4" />}
                  <div className="flex items-start gap-3">
                    <div className={`rounded-full p-2 ${
                      activity.status === 'success' ? 'bg-success/10 text-success' :
                      activity.status === 'info' ? 'bg-info/10 text-info' :
                      'bg-warning/10 text-warning'
                    }`}>
                      {activity.status === 'success' ? <Check className="h-4 w-4" /> :
                       activity.status === 'info' ? <Calendar className="h-4 w-4" /> :
                       <TrendingUp className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium">{activity.content}</p>
                      <p className="text-xs text-muted-foreground flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {activity.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Tweets</CardTitle>
            <CardDescription>
              Your best content this week
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topPerformers.map((tweet, index) => (
                <div key={tweet.id}>
                  {index > 0 && <Separator className="my-4" />}
                  <div className="space-y-2">
                    <p className="text-sm line-clamp-2">{tweet.content}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>❤️ {formatNumber(tweet.likes)}</span>
                      <span>🔁 {formatNumber(tweet.retweets)}</span>
                      <Badge variant="success" className="ml-auto">
                        {formatPercentage(tweet.engagement)}
                      </Badge>
                    </div>
                    <Progress value={tweet.engagement * 100} className="h-1" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks to manage your content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button variant="outline" className="h-auto flex-col py-4 gap-2">
              <Zap className="h-5 w-5" />
              <span className="text-sm">Generate Tweet</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-4 gap-2">
              <Calendar className="h-5 w-5" />
              <span className="text-sm">View Queue</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-4 gap-2">
              <BarChart3 className="h-5 w-5" />
              <span className="text-sm">Analytics</span>
            </Button>
            <Button variant="outline" className="h-auto flex-col py-4 gap-2">
              <TrendingUp className="h-5 w-5" />
              <span className="text-sm">Trends</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </MainLayout>
  )
}
