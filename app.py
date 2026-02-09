import streamlit as st
import warnings
import logging

# Suppress logging errors
logging.raiseExceptions = False

# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv()

# Import the orchestrator
from orchestrator import BlogOrchestrator

# Page configuration
st.set_page_config(
    page_title="AI Blog Orchestrator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        border-color: #FF6B6B;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🤖 AI Blog Orchestrator")
st.markdown("""
Welcome to the AI Blog Orchestrator! This tool uses advanced AI to create well-structured, 
coherent blog posts on any topic you choose.

**How it works:**
1. Enter your blog topic
2. Choose the target length and writing style
3. Click "Generate Blog Post"
4. Review your AI-generated blog with quality analysis
""")

st.divider()

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check if API key is set
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        st.success("✅ API Key Loaded")
    else:
        st.error("❌ API Key Missing")
        st.warning("Please add your GROQ_API_KEY to the .env file")
    
    st.divider()
    
    # About section
    st.header("ℹ️ About")
    st.markdown("""
    This app uses:
    - **Groq API** for fast LLM inference
    - **Llama 3.3 70B** model
    - **Instructor** for structured outputs
    
    Each blog post goes through:
    1. 📋 Planning & Structure
    2. ✍️ Section Writing
    3. 🔍 Quality Review
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Blog Configuration")
    
    # Topic input
    topic = st.text_input(
        "Blog Topic",
        placeholder="e.g., The impact of AI on software development",
        help="Enter the main topic or subject for your blog post"
    )
    
    # Target length
    target_length = st.slider(
        "Target Length (words)",
        min_value=500,
        max_value=3000,
        value=1200,
        step=100,
        help="The approximate word count for your blog post"
    )
    
    # Writing style
    style = st.selectbox(
        "Writing Style",
        options=[
            "technical but accessible",
            "informative",
            "conversational",
            "professional",
            "casual and friendly",
            "academic",
            "persuasive"
        ],
        help="Choose the tone and style for your blog post"
    )

with col2:
    st.header("💡 Tips")
    st.info("""
    **Good topics:**
    - "The future of renewable energy"
    - "Benefits of remote work"
    - "Introduction to blockchain"
    
    **Avoid:**
    - Very broad topics
    - Single-word topics
    - Questions as topics
    """)

st.divider()

# Generate button
if st.button("🚀 Generate Blog Post", type="primary"):
    if not topic:
        st.error("⚠️ Please enter a blog topic!")
    elif not api_key:
        st.error("⚠️ Please configure your GROQ_API_KEY in the .env file!")
    else:
        # Show progress
        with st.spinner("🤖 Initializing AI Orchestrator..."):
            orchestrator = BlogOrchestrator()
        
        # Create progress bar
        progress_text = "Generating your blog post..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Status updates
        status_placeholder = st.empty()
        
        try:
            # Update: Planning
            progress_bar.progress(20, text="📋 Planning blog structure...")
            status_placeholder.info("🔍 Analyzing topic and creating outline...")
            
            # Generate the blog
            result = orchestrator.write_blog(
                topic=topic,
                target_length=target_length,
                style=style
            )
            
            # Update: Complete
            progress_bar.progress(100, text="✅ Blog post generated!")
            status_placeholder.empty()
            
            # Success message
            st.success("🎉 Blog post successfully generated!")
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["📄 Final Blog", "📊 Analysis", "💡 Suggestions"])
            
            with tab1:
                st.header("Final Blog Post")
                
                # Display the blog post with nice formatting
                blog_content = result["review"].final_version
                
                # Split into paragraphs for better display
                paragraphs = blog_content.split('. ')
                formatted_blog = ""
                for i, para in enumerate(paragraphs):
                    if para.strip():
                        formatted_blog += para.strip() + '.\n\n'
                        if (i + 1) % 3 == 0:  # Extra space every 3 sentences
                            formatted_blog += '\n'
                
                st.markdown(formatted_blog)
                
                # Download button
                st.download_button(
                    label="⬇️ Download Blog Post (.txt)",
                    data=blog_content,
                    file_name=f"blog_{topic[:30].replace(' ', '_')}.txt",
                    mime="text/plain"
                )
            
            with tab2:
                st.header("Quality Analysis")
                
                # Cohesion score with visual indicator
                cohesion_score = result["review"].cohesion_score
                st.metric(
                    label="Cohesion Score",
                    value=f"{cohesion_score:.2f}",
                    delta=f"{(cohesion_score - 0.7):.2f} vs. baseline",
                    delta_color="normal"
                )
                
                # Progress bar for score
                score_percentage = int(cohesion_score * 100)
                st.progress(score_percentage, text=f"Quality: {score_percentage}%")
                
                # Interpretation
                if cohesion_score >= 0.9:
                    st.success("🌟 Excellent! The blog sections flow together seamlessly.")
                elif cohesion_score >= 0.8:
                    st.success("✅ Great! The blog is well-structured and coherent.")
                elif cohesion_score >= 0.7:
                    st.info("👍 Good! Minor improvements could enhance flow.")
                else:
                    st.warning("⚠️ Fair. Consider reviewing the suggested edits below.")
                
                # Show structure
                st.subheader("📋 Blog Structure")
                st.json({
                    "Topic": topic,
                    "Target Length": f"{target_length} words",
                    "Style": style,
                    "Sections": len(result["structure"].sections),
                    "Section Types": [s.section_type for s in result["structure"].sections]
                })
            
            with tab3:
                st.header("Editorial Suggestions")
                
                if result["review"].suggested_edits:
                    st.write(f"Found {len(result['review'].suggested_edits)} suggestions to improve your blog:")
                    
                    for i, edit in enumerate(result["review"].suggested_edits, 1):
                        with st.expander(f"📝 {edit.section_name}", expanded=(i == 1)):
                            st.write(f"**Suggestion:**")
                            st.info(edit.suggested_edit)
                else:
                    st.success("🎉 No suggestions! Your blog is ready to publish!")
        
        except Exception as e:
            progress_bar.empty()
            status_placeholder.empty()
            st.error(f"❌ An error occurred: {str(e)}")
            st.error("Please check your API key and try again.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; padding: 2rem;'>
    Made with ❤️ using Streamlit and Groq API<br>
    <small>Powered by Llama 3.3 70B Versatile</small>
</div>
""", unsafe_allow_html=True)