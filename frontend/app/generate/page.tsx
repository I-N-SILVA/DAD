"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Wand2,
  Sparkles,
  Copy,
  RefreshCw,
  Send,
  TrendingUp,
  Check,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

// Form validation schema
const generateFormSchema = z.object({
  topic: z.string().min(3, "Topic must be at least 3 characters").max(100),
  numIdeas: z.number().min(1).max(10),
  tone: z.enum(["professional", "casual", "enthusiastic", "educational", "humorous"]),
  category: z.string().optional(),
})

type GenerateFormData = z.infer<typeof generateFormSchema>

export default function GeneratePage() {
  const { toast } = useToast()
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedTweets, setGeneratedTweets] = useState<any[]>([])
  const [selectedTweet, setSelectedTweet] = useState<number | null>(null)

  const form = useForm<GenerateFormData>({
    resolver: zodResolver(generateFormSchema),
    defaultValues: {
      topic: "",
      numIdeas: 5,
      tone: "professional",
      category: "",
    },
  })

  const handleGenerate = async (data: GenerateFormData) => {
    setIsGenerating(true)

    // Simulate API call
    setTimeout(() => {
      const mockTweets = [
        {
          id: 1,
          content: `The future of ${data.topic} is here! 🚀\n\nHere's what makes it revolutionary:\n• AI-powered automation\n• Real-time insights\n• Seamless integration\n\nThe game is changing. Are you ready?`,
          score: 92,
          grade: "A",
          predictedEngagement: 0.089,
        },
        {
          id: 2,
          content: `Just discovered 5 game-changing facts about ${data.topic}:\n\n1. It's transforming industries\n2. Adoption is skyrocketing\n3. ROI is measurable\n4. It's more accessible than ever\n5. The future starts now\n\nWhich one surprised you most?`,
          score: 88,
          grade: "B+",
          predictedEngagement: 0.082,
        },
        {
          id: 3,
          content: `Hot take: ${data.topic} isn't just a trend—it's the foundation of tomorrow's technology.\n\nHere's why everyone's talking about it... 🧵`,
          score: 85,
          grade: "B",
          predictedEngagement: 0.078,
        },
        {
          id: 4,
          content: `3 reasons why ${data.topic} matters more than you think:\n\n✅ Efficiency gains\n✅ Cost reduction  \n✅ Competitive advantage\n\nIgnore it at your own risk.`,
          score: 79,
          grade: "C+",
          predictedEngagement: 0.071,
        },
        {
          id: 5,
          content: `Breaking: ${data.topic} is revolutionizing how we work.\n\nThe stats don't lie:\n📊 95% adoption rate\n📈 300% productivity boost\n💰 50% cost savings\n\nThe future is now.`,
          score: 91,
          grade: "A-",
          predictedEngagement: 0.087,
        },
      ].slice(0, data.numIdeas)

      setGeneratedTweets(mockTweets)
      setIsGenerating(false)

      toast({
        title: "Success!",
        description: `Generated ${data.numIdeas} tweet ideas`,
        variant: "success",
      })
    }, 2000)
  }

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content)
    toast({
      title: "Copied!",
      description: "Tweet copied to clipboard",
    })
  }

  const handleAddToQueue = (tweet: any) => {
    toast({
      title: "Added to queue!",
      description: "Tweet scheduled for optimal posting time",
      variant: "success",
    })
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return "success"
    if (score >= 70) return "warning"
    return "secondary"
  }

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Generate Content</h1>
        <p className="text-muted-foreground mt-2">
          Create engaging tweets powered by AI and your knowledge base
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" />
              Generation Settings
            </CardTitle>
            <CardDescription>
              Customize your content generation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={form.handleSubmit(handleGenerate)} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="topic" required>Topic</Label>
                <Input
                  id="topic"
                  placeholder="e.g., AI, Machine Learning, Productivity"
                  {...form.register("topic")}
                  error={form.formState.errors.topic?.message}
                />
                <p className="text-xs text-muted-foreground">
                  What do you want to tweet about?
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="numIdeas">Number of Ideas</Label>
                <Input
                  id="numIdeas"
                  type="number"
                  min="1"
                  max="10"
                  {...form.register("numIdeas", { valueAsNumber: true })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tone">Tone</Label>
                <select
                  id="tone"
                  {...form.register("tone")}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="professional">Professional</option>
                  <option value="casual">Casual</option>
                  <option value="enthusiastic">Enthusiastic</option>
                  <option value="educational">Educational</option>
                  <option value="humorous">Humorous</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category (Optional)</Label>
                <Input
                  id="category"
                  placeholder="e.g., Tech, Business, Tips"
                  {...form.register("category")}
                />
              </div>

              <Separator />

              <Button
                type="submit"
                className="w-full"
                loading={isGenerating}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>Generating...</>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Tweets
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Generated Content */}
        <div className="lg:col-span-2 space-y-4">
          {generatedTweets.length === 0 ? (
            <Card className="h-full flex items-center justify-center min-h-[400px]">
              <CardContent className="text-center py-12">
                <Wand2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No tweets generated yet</h3>
                <p className="text-sm text-muted-foreground mb-6">
                  Fill in the form and click "Generate Tweets" to create content
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Badge variant="outline">AI-Powered</Badge>
                  <Badge variant="outline">RAG-Enhanced</Badge>
                  <Badge variant="outline">Pre-Scored</Badge>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList>
                <TabsTrigger value="all">All Ideas ({generatedTweets.length})</TabsTrigger>
                <TabsTrigger value="top">Top Rated</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {generatedTweets.map((tweet, index) => (
                  <Card
                    key={tweet.id}
                    className={cn(
                      "transition-all cursor-pointer hover:shadow-md",
                      selectedTweet === index && "ring-2 ring-primary"
                    )}
                    onClick={() => setSelectedTweet(index)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant={getScoreColor(tweet.score) as any}>
                            Score: {tweet.score}/100 ({tweet.grade})
                          </Badge>
                          <Badge variant="secondary">
                            <TrendingUp className="h-3 w-3 mr-1" />
                            {(tweet.predictedEngagement * 100).toFixed(1)}% predicted
                          </Badge>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCopy(tweet.content)
                            }}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAddToQueue(tweet)
                            }}
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="p-4 rounded-lg bg-muted/50 border">
                        <p className="text-sm whitespace-pre-wrap">{tweet.content}</p>
                      </div>
                      {tweet.score >= 85 && (
                        <div className="mt-4 flex items-center gap-2 text-xs text-success">
                          <Check className="h-3 w-3" />
                          <span>High quality - ready to post!</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>

              <TabsContent value="top" className="space-y-4">
                {generatedTweets
                  .filter((t) => t.score >= 85)
                  .map((tweet, index) => (
                    <Card key={tweet.id} className="hover:shadow-md transition-shadow">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-2">
                            <Badge variant="success">
                              Score: {tweet.score}/100 ({tweet.grade})
                            </Badge>
                            <Badge variant="secondary">
                              <TrendingUp className="h-3 w-3 mr-1" />
                              {(tweet.predictedEngagement * 100).toFixed(1)}%
                            </Badge>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleCopy(tweet.content)}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleAddToQueue(tweet)}
                            >
                              <Send className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="p-4 rounded-lg bg-muted/50 border">
                          <p className="text-sm whitespace-pre-wrap">{tweet.content}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
              </TabsContent>
            </Tabs>
          )}
        </div>
      </div>
    </MainLayout>
  )
}
