from typing import List, Dict
from pydantic import BaseModel, Field
from groq import Groq
import os
import logging
import instructor

# Set up logging cnfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(l;evelname)s - %^(message)s",
)
logger = logging.getLogger(__name__)


client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")))
model = "llama-3.3-70b-versatile"


# Step 1: Define the data models


class SubTask(BaseModel):
    """Blog section task defined by orchestrator"""

    section_type: str = Field(description="Type of blog section to write")
    description: str = Field(description="What this section should cover")
    style_guide: str = Field(description="Writing style for this section")
    target_length: str = Field(description="Target word count for this section")


class OrchestratrPlan(BaseModel):
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

    section_name: str = Field(description="Name of the secton")
    suggested_edit: str = Field(description="Suggested edit")


class ReviewFeedback(BaseModel):
    """ "Final Review and suggestions"""

    cohesion_score: float = Field(description="How well sections flow together (0-1)")
    suggested_edits: List[SuggestedEdits] = Field(
        description="Suggested edits by section"
    )
    final_verion: str = Field(description="Complete, polished blogh post")


# Step 2: Define Prompts

ORCHESTRATOR_PROMPT = """
Analyze this blog topic and break it down into logical sections.

Topic: {topic}
Target Length: {target_length} words
Style: {style}

Return youe response in this format:

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

Return your response in this format:

# Content
[Your section content here, following the style guide]

# Key Points
- Main point 1
- Main point 2
[Additional points as nneeded...]
"""

REVIEWER_PROMPT = """
Review this blog post for cohesion qnd flow:

Topic: {topic}
Target Audience: {audience}

Sections:
{sections}

Provide a cohesion score between 0.0 and 1.0, suggested edits for each section if needed, and a final polished version of the complete post.

The cohesion score should reflect how well the sections flow together, with 1.0 being perfect cohesion.
For suggested edits, focus on improving trasition and maintaining consistent tone across sections.
The final version should incorporate your suggested improuvments into a polished, cohesive blog post.
"""
