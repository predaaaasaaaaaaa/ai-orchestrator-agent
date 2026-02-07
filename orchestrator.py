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


