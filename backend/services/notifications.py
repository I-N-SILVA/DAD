"""
Notification Service

Sends notifications via Mac notifications and email.
"""

import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger
import platform


class NotificationService:
    """
    Multi-channel notification service.

    Supports:
    - Mac OS notifications
    - Email notifications
    - Future: SMS, Slack, Discord
    """

    def __init__(
        self,
        email_enabled: bool = False,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None
    ):
        """
        Initialize notification service.

        Args:
            email_enabled: Enable email notifications
            smtp_server: SMTP server (e.g., smtp.gmail.com)
            smtp_port: SMTP port
            sender_email: Sender email address
            sender_password: Email password/app password
        """
        self.email_enabled = email_enabled
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

        self.is_mac = platform.system() == "Darwin"

        logger.info(f"NotificationService initialized (email={email_enabled}, mac={self.is_mac})")

    def send_mac_notification(
        self,
        title: str,
        message: str,
        sound: bool = True
    ) -> bool:
        """
        Send Mac OS notification.

        Args:
            title: Notification title
            message: Notification message
            sound: Play notification sound

        Returns:
            Success status
        """
        if not self.is_mac:
            logger.warning("Not running on Mac, cannot send Mac notification")
            return False

        try:
            # Use osascript to display notification
            sound_arg = "with sound" if sound else ""
            script = f'display notification "{message}" with title "{title}" {sound_arg}'

            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )

            logger.info(f"Mac notification sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Error sending Mac notification: {e}")
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Send email notification.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            html: Whether body is HTML

        Returns:
            Success status
        """
        if not self.email_enabled:
            logger.warning("Email notifications not enabled")
            return False

        if not all([self.smtp_server, self.sender_email, self.sender_password]):
            logger.error("Email configuration incomplete")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            # Attach body
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')

            msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def notify_trend_detected(self, trend_topic: str, score: float):
        """Notify when a new trend is detected."""
        title = "🔥 New Trend Detected!"
        message = f"#{trend_topic} is trending now (score: {score:.1f})"

        self.send_mac_notification(title, message, sound=True)

    def notify_high_engagement(self, tweet_id: str, engagement_rate: float):
        """Notify when a tweet gets high engagement."""
        title = "🚀 High Engagement!"
        message = f"Your tweet is performing well! {engagement_rate:.1%} engagement rate"

        self.send_mac_notification(title, message, sound=True)

    def notify_mention(self, username: str, preview: str):
        """Notify when mentioned."""
        title = f"💬 Mention from @{username}"
        message = preview[:100]

        self.send_mac_notification(title, message, sound=False)

    def notify_queue_ready(self, num_tweets: int):
        """Notify when tweets are ready for posting."""
        title = "📝 Content Ready"
        message = f"{num_tweets} tweets ready for review and posting"

        self.send_mac_notification(title, message, sound=False)

    def send_weekly_report(
        self,
        to_email: str,
        report_data: dict
    ) -> bool:
        """
        Send weekly performance report via email.

        Args:
            to_email: Recipient email
            report_data: Report data dictionary

        Returns:
            Success status
        """
        subject = f"📊 Weekly Content Report - {report_data.get('period', 'This Week')}"

        # Build HTML email
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1DA1F2;">Weekly Content Report</h2>

            <div style="background: #F5F8FA; padding: 15px; border-radius: 8px; margin: 20px 0;">
              <h3>Summary</h3>
              <p><strong>Total Tweets:</strong> {report_data.get('total_tweets', 0)}</p>
              <p><strong>Total Engagement:</strong> {report_data.get('total_engagement', 0):,}</p>
              <p><strong>Avg Engagement Rate:</strong> {report_data.get('avg_engagement_rate', 0):.2%}</p>
              <p><strong>Follower Growth:</strong> +{report_data.get('follower_growth', 0)}</p>
            </div>

            <div style="margin: 20px 0;">
              <h3>Top Performing Tweet</h3>
              <div style="background: white; border: 1px solid #E1E8ED; padding: 15px; border-radius: 8px;">
                <p>{report_data.get('top_tweet', {}).get('content', 'N/A')[:200]}</p>
                <p style="color: #657786;">
                  ❤️ {report_data.get('top_tweet', {}).get('likes', 0)} |
                  🔁 {report_data.get('top_tweet', {}).get('retweets', 0)} |
                  💬 {report_data.get('top_tweet', {}).get('replies', 0)}
                </p>
              </div>
            </div>

            <div style="margin: 20px 0;">
              <h3>Recommendations</h3>
              <ul>
                {''.join([f'<li>{rec}</li>' for rec in report_data.get('recommendations', [])])}
              </ul>
            </div>

            <p style="color: #657786; font-size: 12px; margin-top: 30px;">
              Generated by X Content RAG System
            </p>
          </body>
        </html>
        """

        return self.send_email(to_email, subject, html, html=True)

    def send_daily_briefing(
        self,
        to_email: str,
        briefing_data: dict
    ) -> bool:
        """
        Send daily briefing via email.

        Args:
            to_email: Recipient email
            briefing_data: Briefing data

        Returns:
            Success status
        """
        subject = "🌅 Daily Content Briefing"

        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1DA1F2;">Daily Content Briefing</h2>

            <div style="margin: 20px 0;">
              <h3>📰 Top News</h3>
              <ul>
                {''.join([f'<li><a href="{article["url"]}">{article["title"]}</a></li>'
                         for article in briefing_data.get('news_articles', [])[:5]])}
              </ul>
            </div>

            <div style="margin: 20px 0;">
              <h3>🔥 Trending Topics</h3>
              <p>
                {'  |  '.join([f"#{trend['name']}" for trend in briefing_data.get('trending_topics', [])[:5]])}
              </p>
            </div>

            <div style="margin: 20px 0;">
              <h3>💡 Tweet Ideas</h3>
              {''.join([f'''
                <div style="background: #F5F8FA; padding: 10px; margin: 10px 0; border-radius: 5px;">
                  <p><strong>{idea["content"]}</strong></p>
                  <p style="color: #657786; font-size: 12px;">
                    {idea["category"]} | Confidence: {idea["confidence"]:.0%}
                  </p>
                </div>
              ''' for idea in briefing_data.get('tweet_ideas', [])[:3]])}
            </div>

            <p style="color: #657786; font-size: 12px; margin-top: 30px;">
              Generated at {briefing_data.get('timestamp', '')}
            </p>
          </body>
        </html>
        """

        return self.send_email(to_email, subject, html, html=True)


# Global notification instance
_notification_service = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance."""
    global _notification_service
    if _notification_service is None:
        from backend.core.config import get_config
        config = get_config()

        _notification_service = NotificationService(
            email_enabled=config.get('notifications.email.enabled', False),
            smtp_server=config.get('notifications.email.smtp_server'),
            smtp_port=config.get('notifications.email.smtp_port', 587),
            sender_email=config.get('notifications.email.sender_email'),
            sender_password=config.get('notifications.email.sender_password')
        )

    return _notification_service


if __name__ == "__main__":
    # Test notifications
    notifier = NotificationService()

    # Test Mac notification
    notifier.send_mac_notification(
        title="Test Notification",
        message="This is a test from X Content RAG System",
        sound=True
    )

    # Test trend notification
    notifier.notify_trend_detected("AI", 95.5)

    # Test engagement notification
    notifier.notify_high_engagement("123456", 0.085)

    print("Notifications sent!")
