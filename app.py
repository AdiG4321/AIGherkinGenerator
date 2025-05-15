import streamlit as st
import sys
import asyncio
import base64
from dotenv import load_dotenv
from datetime import datetime
import yaml
from typing import Dict, Any

from src.Agents.agents import qa_agent 

from src.Utilities.utils import fetch_html_content, parse_html_for_elements, add_uniqueness_context
from langchain_openai import ChatOpenAI

from src.Prompts.agno_prompts import (
    generate_scenarios_from_user_story,
    generate_heading_scenarios_prompt,
    generate_paragraph_scenarios_prompt,
    generate_image_logo_scenarios_prompt,
    generate_icon_scenarios_prompt,
    generate_link_scenarios_prompt,
    generate_button_scenarios_prompt,
    generate_form_scenarios_prompt,
)

# Load environment variables
load_dotenv()

# --- Load Configuration --- 
def load_config():
    try:
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        st.error("Error: config.yaml not found! Please ensure it exists in the project root.")
        config = {} # Return empty dict to avoid further errors, or handle differently
    except yaml.YAMLError as e:
        st.error(f"Error parsing config.yaml: {e}")
        config = {}
    return config

config = load_config()
# --- End Load Configuration ---

# Handle Windows asyncio policy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def main():

    st.set_page_config(page_title="ScenarioCraft AI", layout="wide") # Renamed page title

    # Initialize session state for Tab 1 (User Story)
    if "edited_steps" not in st.session_state:
        st.session_state.edited_steps = None
    if "changes_saved" not in st.session_state:
        st.session_state.changes_saved = False

    # Initialize session state for Tab 2 (URL) - Already done, but good practice to keep initializations together
    if "url_gherkin_scenarios" not in st.session_state: # Stores original generation
        st.session_state.url_gherkin_scenarios = None
    if "edited_url_steps" not in st.session_state: # Stores edited version
        st.session_state.edited_url_steps = None
    if "url_generation_error" not in st.session_state:
        st.session_state.url_generation_error = None
    if "url_changes_saved" not in st.session_state:
        st.session_state.url_changes_saved = False
    if "url_scenario_counts" not in st.session_state: # Initialize count state
        st.session_state.url_scenario_counts = None

    # Add logo using Base64 encoding for potentially better clarity
    try:
        with open("src/logo/Newpage_logo.png", "rb") as f:
            img_bytes = f.read()
        b64_string = base64.b64encode(img_bytes).decode()
        logo_html = f'<img src="data:image/png;base64,{b64_string}" width="150">'
        st.markdown(logo_html, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Logo file not found at src/logo/Newpage_logo.png")
    except Exception as e:
        st.warning(f"Could not load logo: {e}")

    # Apply custom CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

    /* General App Styling */
    .stApp {
        font-family: 'Poppins', sans-serif;
        background-color: #87CEEB; /* Sky blue background */
        color: #333333;
        padding: 2rem;
    }

    /* Navigation Bar Styling */
    .header {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0.3rem 2rem;
        background-color: #4682B4; /* Steel blue for header */
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem; /* Reduced bottom margin */
    }

    .header-item {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 600;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        text-align: center;
        transition: background 0.3s ease, transform 0.3s ease;
    }

    .header-item:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-3px);
    }

    /* Button Styling */
    .stButton > button {
        background-color: #4682B4; /* Steel blue for buttons */
        color: #FFFFFF;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        border: none;
        transition: background 0.3s ease, transform 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #5F9EA0; /* Cadet blue on hover */
        transform: scale(1.05);
    }

    /* Input Fields Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #F0F8FF; /* Alice blue for input fields */
        border: 1px solid #4682B4;
        color: #333333;
        border-radius: 8px;
        padding: 0.6rem;
        transition: border 0.3s ease, box-shadow 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4682B4;
        box-shadow: 0 0 8px rgba(70, 130, 180, 0.6);
    }

    /* Form Controls Styling */
    .stRadio > div {
        background-color: #F0F8FF;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .stRadio > div:hover {
        background-color: #E6F3FF;
    }

    /* Grid Layout Styling */
    .stContainer {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
    }

    /* Footer Styling */
    .footer {
        text-align: center;
        padding: 1rem;
        background-color: #4682B4;
        border-radius: 10px;
        margin-top: 3rem;
        box-shadow: 0 -4px 15px rgba(0, 0, 0, 0.2);
        color: white;
    }
    
    .main-title {
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-size: 45px;
        font-weight: 600;
        color: #333333;
        padding: 10px 0;
        margin-bottom: 20px;
        border-bottom: 2px solid #4682B4;
        width: 100%;
        box-sizing: border-box;
    }

    .subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: 24px;
        color: #333333;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 400;
    }

    .code-container {
        background-color: #F8F8FF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }

    .glow-text {
        color: #4682B4;
    }

    .sidebar-heading {
        background-color: #4682B4;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        color: white;
    }

    .status-success {
        background-color: #90EE90;
        color: #333333;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 15px 0;
    }

    .status-error {
        background-color: #FFA07A;
        color: #333333;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 15px 0;
    }

    .tab-container {
        background-color: #F0F8FF;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }

    .download-btn {
        background-color: #4682B4;
        color: white;
        text-align: center;
        padding: 12px 20px;
        border-radius: 30px;
        font-weight: 600;
        display: block;
        margin: 20px auto;
        width: fit-content;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .download-btn:hover {
        background-color: #5F9EA0;
        transform: scale(1.05);
        box-shadow: 0 12px 20px rgba(0, 0, 0, 0.15);
    }

    .fade-in {
        animation: fadeIn 1.5s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Spinner styling */
    .stSpinner > div > div {
        border-color: #4682B4 #4682B4 transparent !important;
    }

    /* ADDED: Style for selected items in multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #2E8B57; /* SeaGreen */
        color: white; /* Ensure text is readable */
        border-color: #2E8B57; /* Match border color */
        border-radius: 0.5rem; /* Match button radius */
    }
    </style>
    """, unsafe_allow_html=True)

    # Custom Header
    st.markdown('<div class="header fade-in"><span class="header-item">AI-Powered Gherkin Scenario Generator</span></div>', unsafe_allow_html=True) # Changed Header text
    
    # Main Title with custom styling
    st.markdown('<h1 class="main-title fade-in">AI Gherkin Studio</h1>', unsafe_allow_html=True) # Changed Main Title
    st.markdown('<p class="subtitle fade-in">Generate Comprehensive Gherkin from User Stories and URLs</p>', unsafe_allow_html=True) # Changed Subtitle
    # Sidebar styling
    with st.sidebar:
        # Sidebar Heading
        st.markdown('<div class="sidebar-heading">ScenarioCraft AI</div>', unsafe_allow_html=True)

        # Renamed About section expander
        with st.expander("About ScenarioCraft AI"):
            tab1, tab2, tab3, tab4 = st.tabs([
                "Vision & Mission", 
                "Features", 
                "How It Works",
                "Benefits"
            ])
            
            with tab1:
                st.subheader("Our Vision")
                st.write("To be the leading AI solution for effortlessly creating comprehensive and accurate Gherkin scenarios, accelerating behavior-driven development.")
                
                st.subheader("Our Mission")
                st.write("Empower development and QA teams to generate high-quality, maintainable Gherkin feature files rapidly from requirements or existing web interfaces using advanced AI.")
            
            with tab2:
                st.markdown("#### 🧠 AI Gherkin Generation (User Story)")
                st.write("Automatically convert user stories into detailed Gherkin scenarios (positive, negative, edge cases).")
                st.markdown("#### 📄 AI Gherkin Generation (URL)")
                st.write("Analyze a website URL to generate Gherkin scenarios for verifying key UI elements (headings, links, images, icons, etc.).")
                st.markdown("#### 🔍 Intelligent Element Analysis")
                st.write("Automatically identifies and extracts relevant web element details from a URL for scenario generation.")
                st.markdown("#### ✏️ Gherkin Scenario Editor")
                st.write("Review and refine generated Gherkin scenarios directly within the application.")
                st.markdown("#### 💾 Downloadable Feature Files")
                st.write("Easily download generated scenarios as standard `.feature` files.")

            with tab3: # How it works - seems ok after previous edits
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.markdown("### 1")
                with col2:
                    st.markdown("#### Provide Input")
                    st.write("Enter a User Story or a Website URL.")
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.markdown("### 2")
                with col2:
                    st.markdown("#### Generate")
                    st.write("Let our AI analyze your input and generate Gherkin scenarios.")
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.markdown("### 3")
                with col2:
                    st.markdown("#### Review & Download")
                    st.write("Review the generated Gherkin, edit if needed, and download the .feature file.")

            with tab4: # Benefits - seems ok after previous edits
                st.write("• Significant reduction in time-to-generate Gherkin")
                st.write("• Enhanced scenario coverage")
                st.write("• Consistent Gherkin syntax and structure")
                st.write("• Lower maintenance overhead for feature files")
                st.write("• Preserves testing knowledge in a clear format")
            
    
    # Main content area - Introduce Tabs
    tab1, tab2 = st.tabs(["Generate from User Story", "Generate from URL"])

    with tab1:
        st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">Enter User Story</h3>', unsafe_allow_html=True)
        user_story = st.text_area(
            "User Story Input",
            placeholder="e.g., As a user, I want to log in with valid credentials so that I can access my account.",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Buttons with better layout
        generate_btn = st.button("🔍 Generate Gherkin")

        # Gherkin Generation Section
        if generate_btn and user_story:
            with st.spinner("Generating Gherkin scenarios..."):
                prompt = generate_scenarios_from_user_story(user_story)
                run_response = qa_agent.run(prompt)
                generated_steps = run_response.content
                
                # Initialize both generated_steps and edited_steps in session state
                st.session_state.generated_steps = generated_steps
                st.session_state.edited_steps = generated_steps
                st.session_state.changes_saved = False # Reset save status on new generation
                
                st.markdown('<div class="status-success fade-in">Gherkin scenarios generated successfully!</div>', unsafe_allow_html=True)
        
        # Display scenarios editor or code block based on save state
        if "edited_steps" in st.session_state:
            st.markdown('<div class="card code-container fade-in">', unsafe_allow_html=True)
            st.markdown('<h3 class="glow-text">Your Gherkin Scenarios</h3>', unsafe_allow_html=True)
            
            # Check if changes have been saved
            if not st.session_state.get("changes_saved", False):
                # Show editor if not saved
                edited_steps_area = st.text_area(
                "Edit scenarios if needed:", 
                value=st.session_state.edited_steps, 
                height=300, 
                key="scenario_editor"
            )
            
            # Add a save button and show status
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("💾 Save Changes", key="save_changes_btn"):
                    st.session_state.edited_steps = edited_steps_area
                    st.session_state.changes_saved = True
                    st.rerun()
            
                # Display save status (or unsaved changes warning)
            with col2:
                    # Check for unsaved changes by comparing text area content with saved state
                    if edited_steps_area != st.session_state.edited_steps:
                        st.markdown('<div style="color: #FFA500; font-weight: bold;">* You have unsaved changes</div>', unsafe_allow_html=True)
        else:
            # Show code block if saved
            st.code(st.session_state.edited_steps, language="gherkin")
            st.markdown('<div class="status-success" style="margin: 0;">Changes saved. Generate new scenarios to edit again.</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
                
            # Always Add download button after the editor/code block card, using edited steps
            st.download_button(
                label="📥 Download Gherkin (.feature)",
                data=st.session_state.edited_steps,
                file_name="generated_story_scenarios.feature",
                mime="text/plain",
                key="download_story_gherkin_btn"
            )

    # Placeholders for the new URL generation tab
    with tab2:
        st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">Enter Website URL</h3>', unsafe_allow_html=True)
        target_url = st.text_input(
            "URL:",
            placeholder="e.g., https://www.google.com",
            key="url_input"
        )
        
        # --- ADDED: Category Selection UI ---
        # Define all possible categories that have prompts
        # (Keep this in sync with prompt_mapping later)
        all_possible_categories = [
            "headings", "paragraphs", "links", "buttons", 
            "images_and_logos", "icons", "forms"
        ]
        
        # Get default enabled categories from config, handle potential errors
        default_categories = config.get('scenario_generation', {}).get('enabled_categories_default', [])
        # Filter defaults to only include those currently supported
        valid_defaults = [cat for cat in default_categories if cat in all_possible_categories]

        selected_categories = st.multiselect(
            "Select Element Categories to Generate Scenarios For:",
            options=all_possible_categories,
            default=valid_defaults,
            key="selected_categories_ui",
            label_visibility="collapsed",
            placeholder="Select categories for scenario generation",
        )
        # --- END: Category Selection UI ---
        
        st.markdown('</div>', unsafe_allow_html=True)

        generate_url_scenarios_btn = st.button("🔍 Generate Scenarios from URL")

        if generate_url_scenarios_btn and target_url:
            # Clear previous state
            st.session_state.url_gherkin_scenarios = None
            st.session_state.edited_url_steps = None
            st.session_state.url_generation_error = None
            st.session_state.url_changes_saved = False
            st.session_state.url_scenario_counts = None # Clear counts on new generation
            all_gherkin_snippets = []
            scenario_counts = {} # Initialize dict to store counts for this run
            
            try:
                with st.spinner("Fetching and parsing HTML..."):
                    # 1. Fetch HTML
                    html_content = asyncio.run(fetch_html_content(target_url))
                    if html_content.startswith("Error fetching URL"):
                        raise ValueError(f"Failed to fetch HTML: {html_content}")

                    # 2. Parse HTML 
                    parsed_elements = parse_html_for_elements(html_content, target_url)
                    if "error" in parsed_elements:
                        raise ValueError(f"Failed to parse HTML: {parsed_elements['error']}")
                    if not parsed_elements:
                        raise ValueError("No relevant elements found on the page after parsing.")
                        
                    # 2.5 Add Uniqueness Context (Starting with Paragraphs)
                    if "paragraphs" in parsed_elements:
                        paragraph_context_hierarchy = [
                            'id',                  # Paragraph's own ID
                            'parent.id',           # Parent element's ID
                            'parent_classes',      # Parent element's classes (Added)
                            'sibling_text',        # Text of immediate previous/next sibling (now enhanced)
                            'parent_description',  # Parent tag + class/id 
                            'classes'              # Paragraph's own classes (joined)
                        ]
                        parsed_elements["paragraphs"] = add_uniqueness_context(
                            parsed_elements["paragraphs"], 
                            primary_key='text_snippet',
                            context_hierarchy=paragraph_context_hierarchy
                        )
                        # TODO: Add calls for other element types here later if needed

                    # 2.6 Add Uniqueness Context for Links
                    if "links" in parsed_elements:
                        link_context_hierarchy = [
                            'id',             # Link's own ID (Highest priority)
                            'aria_label',     # Link's aria-label
                            'text',           # Link's text content
                            'href',           # Link's absolute href
                            'parent.id',      # Parent element's ID
                            'parent_classes', # Parent element's classes
                            'sibling_text',   # Text of nearest sibling
                            'classes'         # Link's own classes (Lowest priority)
                        ]
                        # Use 'text' or 'aria_label' as primary, fallback if one is missing?
                        # Let's try 'text' first, as it's often present. Or maybe ID if available?
                        # For now, let's make the primary key flexible: check ID, then aria-label, then text
                        # The uniqueness function needs adjustment for flexible primary key, 
                        # OR we run it multiple times/group differently. 
                        # Simpler: Let's use 'text' as primary for now and rely on hierarchy.
                        # If 'text' is empty but aria-label exists, the grouping might be suboptimal, 
                        # but the hierarchy check should still resolve it using aria-label or id.
                        
                        parsed_elements["links"] = add_uniqueness_context(
                            parsed_elements["links"], 
                            primary_key='text', # Using text as primary grouping, relying on hierarchy for ID/aria-label
                            context_hierarchy=link_context_hierarchy
                        )

                    # 2.7 Add Uniqueness Context for Headings
                    if "headings" in parsed_elements:
                        heading_context_hierarchy = [
                            'id',                  # Heading's own ID
                            'parent.id',           # Parent element's ID
                            'sibling_text',        # Text of nearest sibling
                            'parent_classes',      # Parent element's classes
                            'parent_description',  # Parent tag + class/id 
                            'classes'              # Heading's own classes
                        ]
                        parsed_elements["headings"] = add_uniqueness_context(
                            parsed_elements["headings"], 
                            primary_key='text', # Using text as primary grouping
                            context_hierarchy=heading_context_hierarchy
                        )

                    # 2.8 Add Uniqueness Context for Images/Logos
                    if "images_and_logos" in parsed_elements:
                        image_context_hierarchy = [
                            'alt',                 # Alt text (Often descriptive)
                            'id',                  # Image's own ID
                            'src',                 # Image source URL (Should be unique)
                            'parent.id',           # Parent element's ID
                            'sibling_text',        # Text of nearest sibling
                            'parent_classes',      # Parent element's classes
                            'parent_description',  # Parent tag + class/id 
                            'classes'              # Image's own classes
                        ]
                        parsed_elements["images_and_logos"] = add_uniqueness_context(
                            parsed_elements["images_and_logos"], 
                            primary_key='alt', # Using alt text as primary grouping key
                            context_hierarchy=image_context_hierarchy
                        )

                    # 2.9 Add Uniqueness Context for Icons
                    if "icons" in parsed_elements:
                        # This hierarchy mirrors the logic previously embedded in the icon prompt
                        icon_context_hierarchy = [
                            'aria_label',          # Use aria-label first if present
                            'title',               # SVG title text
                            'text',                # Text content of the icon tag (e.g., material icons)
                            'parent.id',           # Parent element's ID
                            'sibling_text',        # Text of nearest sibling
                            'parent_description',  # Parent tag + class/id 
                            'classes',             # Icon's own classes
                            # 'id'? Icons rarely have own ID, but could add if needed
                        ]
                        # Using aria-label as primary key. If None, they group together 
                        # and hierarchy (title, text, parent.id etc.) attempts to split them.
                        parsed_elements["icons"] = add_uniqueness_context(
                            parsed_elements["icons"], 
                            primary_key='aria_label', 
                            context_hierarchy=icon_context_hierarchy
                        )

                    # 2.10 Add Uniqueness Context for Buttons
                    if "buttons" in parsed_elements:
                        button_context_hierarchy = [
                            'id',                  # Button's own ID
                            'text',                # Button text (or value/aria-label)
                            'name',                # Button's name attribute
                            'type',                # Button type (button, submit, reset)
                            'parent.id',           # Parent element's ID
                            'sibling_text',        # Text of nearest sibling
                            'parent_classes',      # Parent element's classes
                            'parent_description',  # Parent tag + class/id 
                            'classes'              # Button's own classes
                        ]
                        parsed_elements["buttons"] = add_uniqueness_context(
                            parsed_elements["buttons"], 
                            primary_key='text', # Using text as primary grouping key
                            context_hierarchy=button_context_hierarchy
                        )

                st.info("Generating Gherkin scenarios for different element types...")
                with st.spinner("Generating scenarios..."):
                    # 3. Call specialized prompts and agents
                    
                    # Define the mapping between element keys and prompt functions
                    prompt_mapping = {
                        "headings": generate_heading_scenarios_prompt,
                        "paragraphs": generate_paragraph_scenarios_prompt,
                        "images_and_logos": generate_image_logo_scenarios_prompt,
                        "icons": generate_icon_scenarios_prompt,
                        "links": generate_link_scenarios_prompt,
                        "buttons": generate_button_scenarios_prompt,
                        "forms": generate_form_scenarios_prompt
                        # Add mappings for inputs, semantic elements here later
                    }

                    # Filter parsed elements based on UI selection BEFORE calculating total_types
                    elements_to_process = { 
                        k: v for k, v in parsed_elements.items() 
                        if k in prompt_mapping and k in selected_categories and v 
                    }
                    
                    total_types_selected = len(elements_to_process)
                    
                    if total_types_selected == 0:
                         st.warning("No data found for the selected element categories. Try selecting different categories or checking the URL.")
                         # Set error state or handle appropriately
                         st.session_state.url_generation_error = "No data found for selected categories."
                    else:
                        progress_bar = st.progress(0)
                        processed_count = 0
                        
                        for i, (element_type, elements_data) in enumerate(elements_to_process.items()):
                            # No need to check category again, already filtered
                            scenario_counts[element_type] = 0 # Initialize count
                            st.write(f"Generating scenarios for: {element_type.replace('_', ' ').title()}")
                            prompt_func = prompt_mapping[element_type]
                            specialized_prompt = prompt_func(elements_data, target_url)
                            
                            if specialized_prompt:
                                try:
                                    run_response = qa_agent.run(specialized_prompt)
                                    snippet = run_response.content.strip()
                                    if snippet: 
                                        all_gherkin_snippets.append(f"# --- Scenarios for {element_type} ---\n{snippet}")
                                        # Count scenarios in the snippet
                                        num_scenarios_in_snippet = snippet.count("Scenario:")
                                        scenario_counts[element_type] = num_scenarios_in_snippet
                                except Exception as agent_error:
                                    st.warning(f"Agent failed for {element_type}: {agent_error}. Skipping.")
                                
                            processed_count += 1
                            progress_bar.progress(processed_count / total_types_selected) # Use total_types_selected

                    # 4. Assemble the final Gherkin feature file
                    if not all_gherkin_snippets:
                         st.session_state.url_generation_error = "No scenario snippets were generated by the agents."
                    else:
                        feature_title = f"Feature: Verification of Elements on {target_url}"
                        background = f"  Background:\n    Given the user navigates to \"{target_url}\""
                        final_gherkin = f"{feature_title}\n\n{background}\n\n"
                        final_gherkin += "\n\n".join(all_gherkin_snippets)
                        
                        # Initialize both original and editable state
                        st.session_state.url_gherkin_scenarios = final_gherkin
                        st.session_state.edited_url_steps = final_gherkin 
                        st.session_state.url_scenario_counts = scenario_counts # Save counts to session state
                        st.success("Scenarios generated successfully from URL!")

            except Exception as e:
                st.session_state.url_generation_error = f"An error occurred: {str(e)}"
            
            # Rerun to display results/errors/editor outside the button click block
            st.rerun() 

        # Display errors if any occurred
        if st.session_state.url_generation_error:
            st.markdown(f'<div class="status-error">{st.session_state.url_generation_error}</div>', unsafe_allow_html=True)

        # Display generation stats if available
        if "url_scenario_counts" in st.session_state and st.session_state.url_scenario_counts:
            filtered_counts = {k: v for k, v in st.session_state.url_scenario_counts.items() if v > 0}
            if filtered_counts:
                 with st.expander("Generation Stats", expanded=True):
                    total_scenarios = sum(filtered_counts.values())
                    st.metric("Total Scenarios Generated", total_scenarios)
                    cols = st.columns(len(filtered_counts))
                    i = 0
                    for category, count in filtered_counts.items():
                        with cols[i]:
                            st.metric(category.replace('_', ' ').title(), count)
                            i += 1

        # Display generated Gherkin scenarios from URL using the editor or code block
        if st.session_state.edited_url_steps is not None:
            st.markdown('<div class="card code-container fade-in">', unsafe_allow_html=True)
            st.markdown('<h3 class="glow-text">Generated Gherkin Scenarios (from URL)</h3>', unsafe_allow_html=True)
            
            # Check if URL changes have been saved
            if not st.session_state.get("url_changes_saved", False):
                # Show editor if not saved
                edited_url_steps_area = st.text_area(
                    "Edit scenarios if needed:",
                    value=st.session_state.edited_url_steps,
                    height=400, # Increased height slightly
                    key="url_scenario_editor"
                )
                
                # Add Save button and status display
                col1_url, col2_url = st.columns([1, 3])
                with col1_url:
                    if st.button("💾 Save Changes", key="save_url_changes_btn"):
                        st.session_state.edited_url_steps = edited_url_steps_area
                        st.session_state.url_changes_saved = True
                        st.rerun()
                
                # Display save status (or unsaved changes warning)
                with col2_url:
                    # Check for unsaved changes by comparing text area content with saved state
                    if edited_url_steps_area != st.session_state.edited_url_steps:
                        st.markdown('<div style="color: #FFA500; font-weight: bold;">* You have unsaved changes</div>', unsafe_allow_html=True)
            else:
                 # Show code block if saved
                st.code(st.session_state.edited_url_steps, language="gherkin")
                st.markdown('<div class="status-success" style="margin: 0;">Changes saved. Generate new scenarios to edit again.</div>', unsafe_allow_html=True)
                    
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Always Add Download button after the editor/code block card, using edited content
            st.download_button(
                label="📥 Download Gherkin (.feature)",
                data=st.session_state.edited_url_steps, # Download edited steps
                file_name="generated_url_scenarios.feature",
                mime="text/plain",
                key="download_url_gherkin_btn"
            )

    # Footer remains outside the tabs
    current_year = datetime.now().year # Get current year
    st.markdown(f'<div class="footer fade-in">© {current_year} ScenarioCraft AI | AI-Powered Gherkin Generation</div>', unsafe_allow_html=True) # Updated footer with new name

if __name__ == "__main__":
    main()
