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
    target_length: str = Field(descripiton="Target word count for this section")


class OrchestratrPlan(BaseModel):
    """Orchestrator's blog structure and tasks"""

    topic_analysis: str = Field(descriptin="Analysis of the blog topic")
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
    """ "Final Review qnd suggestions"""

    cohesion_score: float = Field(description="How well sections flow together (0-1)")
    suggested_edits: List[SuggestedEdits] = Field(
        description="Suggested edits by section"
    )
    final_verion: str = Field(description="Complete, polished blogh post")
