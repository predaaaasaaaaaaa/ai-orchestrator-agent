import warnings
import logging

# Suppress all logging errors from other libraries
logging.raiseExceptions = False  # This stops logging errors from being printed

from typing import List, Dict
from pydantic import BaseModel, Field
from groq import Groq
import os
import logging
import instructor

# Set up logging cnfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
model = "llama-3.3-70b-versatile"


# Step 1: Define the data models


class SubTask(BaseModel):
    """Blog section task defined by orchestrator"""

    section_type: str = Field(description="Type of blog section to write")
    description: str = Field(description="What this section should cover")
    style_guide: str = Field(description="Writing style for this section")
    target_length: str = Field(description="Target word count for this section")


class OrchestratorPlan(BaseModel):
    """Orchestrator's blog structure and tasks"""

    topic_analysis: str = Field(description="Analysis of the blog topic")
    target_audience: str = Field(description="Intended audience for the blog")
    sections: List[SubTask] = Field(description="List of the sections to write")


class SectionContent(BaseModel):
    """Content written by a worker"""

    content: str = Field(description="Written content for the section")
    key_points: List[str] = Field(description="Main points covered")


class SuggestedEdits(BaseModel):
    """ "Suggested Edits for a section"""

    section_name: str = Field(description="Name of the section")
    suggested_edit: str = Field(description="Suggested edit")


class ReviewFeedback(BaseModel):
    """ "Final Review and suggestions"""

    cohesion_score: float = Field(description="How well sections flow together (0-1)")
    suggested_edits: List[SuggestedEdits] = Field(
        description="Suggested edits by section"
    )
    final_version: str = Field(description="Complete, polished blog post")


# Step 2: Define Prompts

ORCHESTRATOR_PROMPT = """
Analyze this blog topic and break it down into logical sections.

Topic: {topic}
Target Length: {target_length} words
Style: {style}

Return your response in this format:

# Analysis
Analyze the topic and explain how it should be structured.
Consider the narrative flow and how sections will work together.

# Target Audience
Define the target audience and their interests/needs.

# Sections
## Section 1
- Type: section_type
- Description: what this section should cover
- Style: writing style guidelines

[Additional sections as needed...]
"""

WORKER_PROMPT = """
Write a blog section based on:
Topic: {topic}
Section Type: {section_type}
Section Goal: {description}
Style Guide: {style_guide}
Target Length: {target_length}

Previously Written Sections:
{previous_sections}

Return your response in this format:

# Content
[Your section content here, following the style guide]

# Key Points
- Main point 1
- Main point 2
[Additional points as needed...]
"""

REVIEWER_PROMPT = """
Review this blog post for cohesion and flow:

Topic: {topic}
Target Audience: {audience}

Sections:
{sections}

Provide a cohesion score between 0.0 and 1.0, suggested edits for each section if needed, and a final polished version of the complete post.

The cohesion score should reflect how well the sections flow together, with 1.0 being perfect cohesion.
For suggested edits, focus on improving transition and maintaining consistent tone across sections.
The final version should incorporate your suggested impruvments into a polished, cohesive blog post.
"""


# Step 3: Implement orchestrator


class BlogOrchestrator:
    def __init__(self):
        self.sections_content = {}

    def get_plan(self, topic: str, target_length: int, style: str) -> OrchestratorPlan:
        """Get orchestrator's blog structure plan"""
        result = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": ORCHESTRATOR_PROMPT.format(
                        topic=topic, target_length=target_length, style=style
                    ),
                }
            ],
            response_model=OrchestratorPlan,
        )
        return result

    def write_section(self, topic: str, section: SubTask) -> SectionContent:
        """Worker: Write a specific blog section with context from previous sections.

        Args:
            topic: The main blog topic
            section: SubTask containing section details

        Returns:
            SectionContent: The written content and key points
        """
        # Create content from previously written sections
        previous_sections = "\n\n".join(
            [
                f"=== {section_type} ===\n{content.content}"
                for section_type, content in self.sections_content.items()
            ]
        )

        result_2 = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": WORKER_PROMPT.format(
                        topic=topic,
                        section_type=section.section_type,
                        description=section.description,
                        style_guide=section.style_guide,
                        target_length=section.target_length,
                        previous_sections=previous_sections
                        if previous_sections
                        else "This is the first section.",
                    ),
                }
            ],
            response_model=SectionContent,
        )
        return result_2

    def review_post(self, topic: str, plan: OrchestratorPlan) -> ReviewFeedback:
        """Reviewer: Analyze and improve overall cohesion"""
        sections_text = "\n\n".join(
            [
                f"=== {section_type} ===\n{content.content}"
                for section_type, content in self.sections_content.items()
            ]
        )

        result_3 = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": REVIEWER_PROMPT.format(
                        topic=topic,
                        audience=plan.target_audience,
                        sections=sections_text,
                    ),
                }
            ],
            response_model=ReviewFeedback,
        )
        return result_3

    def write_blog(
        self, topic: str, target_length: int = 1000, style: str = "informative"
    ) -> Dict:
        """Process the entire blog writing task"""
        logger.info(f"Starting blog writing process for: {topic}")

        # Get blog structure plan
        plan = self.get_plan(topic, target_length, style)
        logger.info(f"Blog structure planned: {len(plan.sections)} sections")
        logger.info(f"Blog structure planned: {plan.model_dump_json(indent=2)}")

        # Write each section
        for section in plan.sections:
            logger.info(f"Writing section: {section.section_type}")
            content = self.write_section(topic, section)
            self.sections_content[section.section_type] = content

        # Review and polish
        logger.info("Reviewing full blog post")
        review = self.review_post(topic, plan)

        return {"structure": plan, "sections": self.sections_content, "review": review}


# Step 4: Example usage

if __name__ == "__main__":
    orchestrator = BlogOrchestrator()

    # Example: Technical blog post
    topic = "The impact of AI on software development"
    result = orchestrator.write_blog(
        topic=topic, target_length=1200, style="technical but accessible"
    )

    print("\n" + "=" * 80)
    print("FINAL BLOG POST")
    print("=" * 80 + "\n")

    # Split the final version into paragraphs and print with spacing
    paragraphs = result["review"].final_version.split(". ")
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            print(paragraph.strip() + ".")
            if (i + 1) % 3 == 0:  # Add extra line break every 3 sentences
                print()

    print("\n" + "=" * 80)
    print(f"COHESION SCORE: {result['review'].cohesion_score}")
    print("=" * 80 + "\n")

    if result["review"].suggested_edits:
        print("SUGGESTED EDITS:")
        print("-" * 80)
        for edit in result["review"].suggested_edits:
            print(f"\n📝 Section: {edit.section_name}")
            print(f"   Suggestion: {edit.suggested_edit}")
        print("\n" + "=" * 80)
