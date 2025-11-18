"use client"

import { useState } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Calendar,
  Clock,
  Trash2,
  Edit,
  Send,
  AlertCircle,
  TrendingUp,
} from "lucide-react"
import { formatRelativeTime } from "@/lib/utils"

export default function QueuePage() {
  // Mock data - will be replaced with API calls
  const [queuedTweets] = useState([
    {
      id: 1,
      content: "Just discovered an amazing new feature in our AI system. The results are mind-blowing! 🤯\n\nHere's what makes it special: [Thread 1/5]",
      scheduledFor: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
      category: "AI",
      predictedEngagement: 0.085,
      score: 87,
      status: "scheduled",
    },
    {
      id: 2,
      content: "Quick tip: Always analyze your competitors' content strategy. It's a goldmine of insights! 💎\n\n#ContentMarketing #Strategy",
      scheduledFor: new Date(Date.now() + 6 * 60 * 60 * 1000), // 6 hours from now
      category: "Tips",
      predictedEngagement: 0.072,
      score: 79,
      status: "scheduled",
    },
    {
      id: 3,
      content: "The future of content creation is here, and it's powered by RAG (Retrieval-Augmented Generation).\n\nLet me break it down for you...",
      scheduledFor: new Date(Date.now() + 24 * 60 * 60 * 1000), // 1 day from now
      category: "Education",
      predictedEngagement: 0.091,
      score: 92,
      status: "scheduled",
    },
    {
      id: 4,
      content: "Weekly stats are in! 📊\n\n✅ 150 tweets posted\n✅ 12.5K followers\n✅ 8.5% avg engagement\n\nWhat a week! 🚀",
      scheduledFor: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000), // 3 days from now
      category: "Stats",
      predictedEngagement: 0.068,
      score: 75,
      status: "pending",
    },
  ])

  const getScoreColor = (score: number) => {
    if (score >= 85) return "success"
    if (score >= 70) return "warning"
    return "destructive"
  }

  const getScoreGrade = (score: number) => {
    if (score >= 90) return "A"
    if (score >= 80) return "B"
    if (score >= 70) return "C"
    if (score >= 60) return "D"
    return "F"
  }

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Content Queue</h1>
            <p className="text-muted-foreground mt-2">
              Manage and optimize your scheduled tweets
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <AlertCircle className="h-4 w-4 mr-2" />
              Optimize Queue
            </Button>
            <Button>
              <Send className="h-4 w-4 mr-2" />
              Auto-Schedule
            </Button>
          </div>
        </div>
      </div>

      {/* Queue Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Queued</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{queuedTweets.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Tweets ready to post
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Next Post</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2 hours</div>
            <p className="text-xs text-muted-foreground mt-1">
              {queuedTweets[0]?.scheduledFor.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg Predicted Engagement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8.0%</div>
            <p className="text-xs text-muted-foreground mt-1">
              <TrendingUp className="h-3 w-3 inline mr-1" />
              Above your average
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Queued Tweets */}
      <Card>
        <CardHeader>
          <CardTitle>Scheduled Tweets</CardTitle>
          <CardDescription>
            All tweets in your posting queue, optimized for maximum engagement
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {queuedTweets.map((tweet, index) => (
              <div key={tweet.id}>
                {index > 0 && <Separator className="my-6" />}
                <div className="space-y-4">
                  {/* Tweet Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-xs">
                          {tweet.category}
                        </Badge>
                        <Badge variant={getScoreColor(tweet.score) as any}>
                          Score: {tweet.score}/100 (Grade {getScoreGrade(tweet.score)})
                        </Badge>
                        <Badge variant="secondary">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          {(tweet.predictedEngagement * 100).toFixed(1)}% predicted
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>

                  {/* Tweet Content */}
                  <div className="p-4 rounded-lg bg-muted/50 border">
                    <p className="text-sm whitespace-pre-wrap">{tweet.content}</p>
                  </div>

                  {/* Tweet Footer */}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="h-4 w-4" />
                      <span>{tweet.scheduledFor.toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-4 w-4" />
                      <span>{tweet.scheduledFor.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div className="flex items-center gap-1.5 ml-auto">
                      <span className="text-xs">Posting in {formatRelativeTime(tweet.scheduledFor)}</span>
                    </div>
                  </div>

                  {/* ML Insights */}
                  {tweet.score >= 85 && (
                    <div className="flex items-start gap-2 p-3 rounded-lg bg-success/10 border border-success/20">
                      <TrendingUp className="h-4 w-4 text-success mt-0.5" />
                      <div className="flex-1">
                        <p className="text-xs font-medium text-success">High Performance Prediction</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          This tweet is predicted to perform {Math.round((tweet.predictedEngagement / 0.072) * 100)}% better than your average
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </MainLayout>
  )
}
