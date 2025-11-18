"use client"

import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  TrendingUp,
  Clock,
  Hash,
  MessageSquare,
  BarChart3,
} from "lucide-react"
import { formatNumber, formatPercentage } from "@/lib/utils"

export default function AnalyticsPage() {
  // Mock data - will be replaced with API calls
  const insights = [
    {
      title: "Optimal Tweet Length",
      description: "Your best tweets average 18 words (±3)",
      icon: MessageSquare,
      stat: "18 words",
      trend: "+2 words",
      recommendation: "Keep tweets concise and focused",
    },
    {
      title: "Best Posting Times",
      description: "Highest engagement during these hours",
      icon: Clock,
      stat: "9AM, 12PM, 5PM",
      trend: "Consistent pattern",
      recommendation: "Schedule posts around these times",
    },
    {
      title: "Top Hashtags",
      description: "Most effective hashtags for engagement",
      icon: Hash,
      stat: "#AI, #Tech, #ML",
      trend: "+15% engagement",
      recommendation: "Use 2-3 relevant hashtags per tweet",
    },
    {
      title: "Engagement Rate",
      description: "Average across all tweets this month",
      icon: TrendingUp,
      stat: "7.2%",
      trend: "+0.8% vs last month",
      recommendation: "Above industry average!",
    },
  ]

  const topHashtags = [
    { tag: "#AI", uses: 45, engagement: 0.089 },
    { tag: "#MachineLearning", uses: 32, engagement: 0.076 },
    { tag: "#Tech", uses: 28, engagement: 0.072 },
    { tag: "#ContentCreation", uses: 24, engagement: 0.068 },
    { tag: "#Automation", uses: 19, engagement: 0.064 },
  ]

  const contentPatterns = [
    { pattern: "Questions", percentage: 32, engagement: 0.092, example: "What's your favorite AI tool?" },
    { pattern: "Lists", percentage: 28, engagement: 0.085, example: "5 ways to improve..." },
    { pattern: "How-to", percentage: 24, engagement: 0.078, example: "How to set up..." },
    { pattern: "Statistics", percentage: 16, engagement: 0.071, example: "95% of users..." },
  ]

  const recommendations = [
    "Post more questions to drive engagement",
    "Tweets with media get 3x more engagement",
    "Optimal posting frequency: 3-4 tweets per day",
    "Your audience is most active on weekdays",
    "Thread format performs well for your niche",
  ]

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Analytics & Insights</h1>
            <p className="text-muted-foreground mt-2">
              Understand what works and optimize your content strategy
            </p>
          </div>
          <Badge variant="success" className="h-8">
            <BarChart3 className="h-4 w-4 mr-1" />
            Real-time Data
          </Badge>
        </div>
      </div>

      {/* Key Insights Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {insights.map((insight) => (
          <Card key={insight.title} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <insight.icon className="h-5 w-5 text-primary" />
                <Badge variant="secondary" className="text-xs">
                  {insight.trend}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">{insight.title}</p>
                <p className="text-2xl font-bold">{insight.stat}</p>
                <p className="text-xs text-muted-foreground">{insight.description}</p>
                <Separator className="my-2" />
                <p className="text-xs text-info">💡 {insight.recommendation}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs for detailed analytics */}
      <Tabs defaultValue="hashtags" className="space-y-4">
        <TabsList>
          <TabsTrigger value="hashtags">Top Hashtags</TabsTrigger>
          <TabsTrigger value="patterns">Content Patterns</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="hashtags" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Hashtags</CardTitle>
              <CardDescription>
                Hashtags ranked by engagement rate and usage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topHashtags.map((item, index) => (
                  <div key={item.tag}>
                    {index > 0 && <Separator className="my-4" />}
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="text-sm font-medium">{item.tag}</p>
                        <p className="text-xs text-muted-foreground">
                          Used {item.uses} times
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="success">
                          {formatPercentage(item.engagement)} engagement
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Content Structure Patterns</CardTitle>
              <CardDescription>
                Analyze what content formats work best
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {contentPatterns.map((item, index) => (
                  <div key={item.pattern}>
                    {index > 0 && <Separator className="my-4" />}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{item.pattern}</p>
                        <Badge variant="info">
                          {formatPercentage(item.engagement)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{item.percentage}% of your content</span>
                        <span>•</span>
                        <span className="italic">"{item.example}"</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Recommendations</CardTitle>
              <CardDescription>
                Actionable insights to improve your content performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recommendations.map((rec, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                      {index + 1}
                    </div>
                    <p className="text-sm flex-1 pt-0.5">{rec}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </MainLayout>
  )
}
