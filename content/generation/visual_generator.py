"""
Visual Content Generator

Generates images, quote cards, and visual content for tweets.
"""

from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
from loguru import logger

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logger.warning("PIL not installed. Run: pip install Pillow")
    Image = None


class VisualContentGenerator:
    """
    Generate visual content for social media.

    Features:
    - Quote cards
    - Stats visualizations
    - Thread previews
    - Simple graphics
    """

    def __init__(self, output_dir: str = "data/generated_images"):
        """
        Initialize visual generator.

        Args:
            output_dir: Directory to save generated images
        """
        if not Image:
            raise ImportError("PIL required. Install: pip install Pillow")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("VisualContentGenerator initialized")

    def generate_quote_card(
        self,
        text: str,
        author: str = "",
        style: str = "minimal",
        size: Tuple[int, int] = (1200, 675)
    ) -> str:
        """
        Generate a quote card image.

        Args:
            text: Quote text
            author: Author name (optional)
            style: Visual style (minimal, bold, gradient)
            size: Image size (width, height)

        Returns:
            Path to generated image
        """
        logger.info(f"Generating quote card ({style} style)...")

        # Create image
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)

        # Load fonts (fallback to default if custom not available)
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Style-specific backgrounds
        if style == "minimal":
            # White background with subtle border
            draw.rectangle([20, 20, size[0]-20, size[1]-20], outline='#1DA1F2', width=4)
            text_color = '#14171A'
        elif style == "bold":
            # Colored background
            img = Image.new('RGB', size, color='#1DA1F2')
            draw = ImageDraw.Draw(img)
            text_color = 'white'
        elif style == "gradient":
            # Simple two-color gradient simulation
            for y in range(size[1]):
                color = self._interpolate_color((26, 161, 242), (29, 209, 161), y / size[1])
                draw.line([(0, y), (size[0], y)], fill=color)
            text_color = 'white'
        else:
            text_color = '#14171A'

        # Wrap text
        wrapped_text = self._wrap_text(text, font_large, size[0] - 100)

        # Draw text
        y_offset = (size[1] - len(wrapped_text) * 70) // 2
        for line in wrapped_text:
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (size[0] - text_width) // 2
            draw.text((x, y_offset), line, fill=text_color, font=font_large)
            y_offset += 70

        # Draw author
        if author:
            bbox = draw.textbbox((0, 0), f"— {author}", font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (size[0] - text_width) // 2
            draw.text((x, size[1] - 80), f"— {author}", fill=text_color, font=font_small)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quote_{timestamp}.png"
        filepath = self.output_dir / filename
        img.save(filepath, 'PNG')

        logger.info(f"Quote card saved: {filepath}")
        return str(filepath)

    def generate_stats_card(
        self,
        stats: dict,
        title: str = "Stats",
        size: Tuple[int, int] = (1200, 675)
    ) -> str:
        """
        Generate a stats visualization card.

        Args:
            stats: Dict of stat_name: value
            title: Card title
            size: Image size

        Returns:
            Path to generated image
        """
        logger.info("Generating stats card...")

        # Create image
        img = Image.new('RGB', size, color='#F5F8FA')
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 70)
            font_stat = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
            font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        except:
            font_title = font_stat = font_label = ImageFont.load_default()

        # Draw title
        bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, 50), title, fill='#14171A', font=font_title)

        # Draw stats
        num_stats = len(stats)
        stat_width = size[0] // num_stats
        y_offset = 200

        for i, (label, value) in enumerate(stats.items()):
            x_center = stat_width * i + stat_width // 2

            # Draw value
            value_text = str(value)
            bbox = draw.textbbox((0, 0), value_text, font=font_stat)
            text_width = bbox[2] - bbox[0]
            draw.text((x_center - text_width // 2, y_offset), value_text,
                     fill='#1DA1F2', font=font_stat)

            # Draw label
            bbox = draw.textbbox((0, 0), label, font=font_label)
            text_width = bbox[2] - bbox[0]
            draw.text((x_center - text_width // 2, y_offset + 80), label,
                     fill='#657786', font=font_label)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stats_{timestamp}.png"
        filepath = self.output_dir / filename
        img.save(filepath, 'PNG')

        logger.info(f"Stats card saved: {filepath}")
        return str(filepath)

    def generate_thread_preview(
        self,
        tweets: list,
        size: Tuple[int, int] = (1200, 1600)
    ) -> str:
        """
        Generate a thread unroll preview image.

        Args:
            tweets: List of tweet texts
            size: Image size

        Returns:
            Path to generated image
        """
        logger.info(f"Generating thread preview ({len(tweets)} tweets)...")

        # Create tall image for thread
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)

        try:
            font_tweet = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 35)
            font_number = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 25)
        except:
            font_tweet = font_number = ImageFont.load_default()

        y_offset = 40

        for i, tweet in enumerate(tweets, 1):
            # Draw tweet number
            number_text = f"{i}/{len(tweets)}"
            draw.text((40, y_offset), number_text, fill='#657786', font=font_number)

            # Draw tweet text
            wrapped = self._wrap_text(tweet, font_tweet, size[0] - 100)
            for line in wrapped:
                y_offset += 45
                draw.text((40, y_offset), line, fill='#14171A', font=font_tweet)

            # Draw separator
            y_offset += 60
            if i < len(tweets):
                draw.line([(40, y_offset), (size[0] - 40, y_offset)],
                         fill='#E1E8ED', width=2)
                y_offset += 40

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"thread_{timestamp}.png"
        filepath = self.output_dir / filename
        img.save(filepath, 'PNG')

        logger.info(f"Thread preview saved: {filepath}")
        return str(filepath)

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Get text bbox to check width
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox(
                (0, 0), test_line, font=font
            )
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _interpolate_color(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        t: float
    ) -> Tuple[int, int, int]:
        """Interpolate between two colors."""
        return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))


if __name__ == "__main__":
    # Test visual generator
    generator = VisualContentGenerator()

    # Generate quote card
    quote_path = generator.generate_quote_card(
        text="The best time to start was yesterday. The next best time is now.",
        author="Ancient Proverb",
        style="minimal"
    )
    print(f"Quote card: {quote_path}")

    # Generate stats card
    stats_path = generator.generate_stats_card(
        stats={
            "Tweets": 150,
            "Followers": "12.5K",
            "Engagement": "8.5%"
        },
        title="Monthly Stats"
    )
    print(f"Stats card: {stats_path}")

    # Generate thread preview
    thread_path = generator.generate_thread_preview([
        "1/ Here's an amazing thread about AI",
        "2/ First, let's talk about the basics",
        "3/ Machine learning is a subset of AI",
        "4/ It enables computers to learn from data"
    ])
    print(f"Thread preview: {thread_path}")
