from typing import Dict, Any, List
import json
from urllib.parse import urlparse

def generate_scenarios_from_user_story(user_story: str) -> str:
    """Generate Gherkin scenarios from a user story"""
    prompt = f"""
    Convert the following user story into comprehensive Gherkin test scenarios.
    Include positive and negative test cases, edge cases, and boundary conditions.
    
    User Story:
    {user_story}
    
    Requirements:
    - Use proper Gherkin syntax with Feature, Scenario, Given, When, Then
    - Add descriptive scenario titles
    - Include tags for organization
    - Create at least 3-5 scenarios covering different cases
    - Focus on functional requirements
    """
    return prompt

# --- Specialized Gherkin Snippet Generation Prompts ---

def generate_heading_scenarios_prompt(heading_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for headings, using DOM context."""
    if not heading_data:
        return ""
    prompt = f"""
    Based on the following heading elements extracted from {url}, generate comprehensive Gherkin scenario snippets for each heading. Each object includes complete DOM context that shows the heading's position in the page structure, including parent elements, ancestors, siblings, and any interactive elements that need to be interacted with before reaching the heading.

    **Goal:** Analyze the DOM context for each heading and generate scenarios that include ALL necessary steps to verify the heading's visibility and content, including any required interactions with parent elements (menus, dropdowns, accordions, etc.).

    **Input Data Structure Example:**
    {{
        "dom_context": {{
            "element": {{
      "tag": "h2",
                "attributes": {{"class": "section-title"}},
                "classes": ["section-title"],
                "id": "section-1",
                "aria_label": "Section One",
      "text": "Section Title",
                "role": "heading"
            }},
            "parent": {{
                "tag": "section",
                "attributes": {{"class": "content-section"}},
                "classes": ["content-section"],
                "id": "main-content",
                "role": "region"
            }},
            "ancestors": [
                {{
                    "tag": "div",
                    "attributes": {{"class": "page-content"}},
                    "classes": ["page-content"],
                    "id": "content-area"
                }}
            ],
            "siblings": {{
                "previous": [
                    {{
                        "tag": "p",
                        "attributes": {{"class": "intro"}},
                        "classes": ["intro"],
                        "text": "Introduction paragraph..."
                    }}
                ],
                "next": [
                    {{
                        "tag": "p",
                        "attributes": {{"class": "content"}},
                        "classes": ["content"],
                        "text": "First paragraph of section..."
                    }}
                ]
            }},
            "children": [],
            "interactive_parents": [
                {{
                    "tag": "button",
                    "attributes": {{"class": "section-toggle"}},
                    "classes": ["section-toggle"],
                    "role": "button",
                    "aria_expanded": "false",
                    "aria_controls": "section-1"
                }}
            ]
        }},
        "sequential_index": 1
    }}

    **Rules for Scenario Generation:**

    1. **Analyze DOM Context:**
       - Check for interactive parents (buttons, links, etc.) that need to be clicked first
       - Look for parent elements with roles like 'menu', 'tablist', 'accordion'
       - Identify any elements with aria-expanded that need to be expanded
       - Note any aria-controls relationships that indicate parent-child interactions

    2. **Generate Steps in Order:**
       - Start with any required parent interactions (e.g., clicking menu buttons)
       - Include steps for expanding/collapsing containers
       - Add steps for navigating through menus/dropdowns
       - End with the heading visibility verification

    3. **Common Patterns to Handle:**
       - Accordion Navigation:
         ```gherkin
         Then the user should see the accordion header
         When the user clicks the accordion header
         Then the accordion content should be expanded
         Then the user should see the heading "Section Title"
         ```

       - Tab Navigation:
         ```gherkin
         Then the user should see the "[Tab Name]" tab
         When the user clicks the "[Tab Name]" tab
         Then the tab content should be visible
         Then the user should see the heading "Section Title"
         ```

       - Menu Navigation:
         ```gherkin
         Given the user is on the homepage
         When the user clicks the menu icon
         Then the first-level menu should be visible
         When the user clicks on "[Menu Button]" button
         Then the second-level menu should be visible with title "[Menu Title]"
         Then the user should see the heading "Section Title"
         ```

    **Rules for Heading Identification:**
    1. Use the most specific identifier available in this order:
       - ID if present
       - aria-label if present
       - text content
       - parent context (e.g., "in the navigation", "in the accordion")
    2. Add context from DOM structure to make the identification unique
    3. Use parent/sibling information to create meaningful scenario titles

    **Rules for Scenario Titles:**
    - Include the complete path to the heading (e.g., "in Main Menu > Products > Section Title")
    - Mention any special containers (e.g., "in accordion", "in dropdown")
    - Include the heading level (h1-h6) if relevant for context

    Extracted Headings (Input Data):
    {json.dumps(heading_data, indent=2)}

    Requirements:
    - Generate one `@heading @visibility` tagged `Scenario:` block for EACH item in the input list
    - Analyze the DOM context to determine all required interactions
    - Include ALL necessary steps to reach and verify the heading
    - Generate clear and descriptive scenario titles that reflect the complete path
    - Always use the most specific identifier available for the heading

    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

def generate_paragraph_scenarios_prompt(paragraph_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for paragraphs, using pre-calculated uniqueness context."""
    if not paragraph_data:
        return ""
    prompt = f"""
    Based on the following paragraph elements extracted from {url}, generate a Gherkin scenario snippet FOR EACH paragraph object in the list. Each object includes a `text_snippet` and potentially a `uniqueness_context` dictionary if needed for disambiguation.

    **Goal:** Generate a clear Scenario and `Then` step for each paragraph. Use the `text_snippet` as the base. If `uniqueness_context` is present, add its details to make the step uniquely identifiable.

    **Input Data Structure:**
    Each item in the list is a dictionary like:
    {{
      "tag": "p",
      "text_snippet": "Example text...",
      "id": "para-id-123", 
      "classes": ["info", "highlight"],
      "parent": {{ "tag": "div", "classes": [], "id": "content-area" }},
      "prev_sibling_text": "Previous heading",
      "next_sibling_text": None,
      "sequential_index": 0,
      "uniqueness_context": {{ "level": "parent.id", "value": "content-area" }} # Optional: Only present if needed
    }}

    **Rules for `Then` Step Generation:**
    1. Start with the `text_snippet`: `Then the user should see the paragraph starting with "TEXT_SNIPPET..."`
    2. Check if `uniqueness_context` exists for the paragraph.
    3. **If `uniqueness_context` exists:** Append the context to the `Then` step based on the `level` key:
        - `id`: Append ` identified by ID "VALUE"`
        - `parent.id`: Append ` within the element with ID "VALUE"`
        - `parent_classes`: Append ` within an element with classes "VALUE"`
        - `sibling_text`: Append ` next to the text "VALUE"` (or `previous to the text "VALUE"`)
        - `parent_description`: Append ` within the VALUE` (e.g., `within the div with classes "info-box"`)
        - `classes`: Append ` with classes "VALUE"`
    4. **If `uniqueness_context` does NOT exist:** Use only the `text_snippet` description from step 1.

    **Rules for Scenario Title Generation:**
    - Create a user-friendly title reflecting the final unique identification used in the `Then` step.
    - Start with "Verify visibility of the paragraph starting with 'SNIPPET...'".
    - If `uniqueness_context` was used, add a concise description of the context:
        - `id`: "... with ID VALUE"
        - `parent.id`: "... within element ID VALUE"
        - `parent_classes`: "... within parent with classes VALUE"
        - `sibling_text`: "... next to text 'VALUE'"
        - `parent_description`: "... within VALUE"
        - `classes`: "... with classes VALUE"
    - **DO NOT include the overall `sequential_index` from the input data.** Use the occurrence number from `uniqueness_context.value` if the level is `sequential_index`.

    Extracted Paragraphs (Input Data with potential uniqueness_context):
    {json.dumps(paragraph_data, indent=2)}

    Requirements:
    - Generate one `@paragraph @visibility @content` tagged `Scenario:` block for EACH item in the input list.
    - Follow the rules above precisely to create a unique and descriptive `Then` step using the `text_snippet` and the provided `uniqueness_context` if available.
    - Generate a user-friendly scenario title based on the final `Then` step description.

    Example Snippets:

      @paragraph @visibility @content
      Scenario: Verify visibility of the paragraph starting with "This is the main description..."
        Then the user should see the paragraph starting with "This is the main description of our product, detailing its features..."

      @paragraph @visibility @content
      Scenario: Verify visibility of the paragraph starting with "Learn More..." within element ID features-section
        Then the user should see the paragraph starting with "Learn More..." within the element with ID "features-section"
        
      @paragraph @visibility @content
      Scenario: Verify visibility of the paragraph starting with "Learn More..." next to the text "Pricing"
        Then the user should see the paragraph starting with "Learn More..." next to the text "Pricing"
        
      @paragraph @visibility @content
      Scenario: Verify visibility of the paragraph starting with "Your request was processed..." identified by ID user-alert-1
        Then the user should see the paragraph starting with "Your request was processed..." identified by ID "user-alert-1"
        
      @paragraph @visibility @content
      Scenario: Verify visibility of the paragraph starting with "All rights reserved..." with classes "text-muted small-font"
        Then the user should see the paragraph starting with "All rights reserved..." with classes "text-muted small-font"

    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

def generate_image_logo_scenarios_prompt(image_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for images and logos, using pre-calculated uniqueness context."""
    if not image_data:
        return ""
    prompt = f"""
    Based on the following image/logo elements extracted from {url}, generate a Gherkin scenario snippet FOR EACH element in the list. Each object includes `alt` text, `src`, `id`, `classes`, `is_likely_logo`, `is_clickable`, `parent_href`, and potentially a `uniqueness_context` dictionary.

    **Goal:** Generate a clear Scenario. 
    - If the image is NOT clickable, generate a `Then` step for visibility.
    - If the image IS clickable, generate `Then` (visibility), `When` (click), and `Then` (navigation/outcome) steps.
    Use the `alt` text or `src` as the base identifier. If `uniqueness_context` is present, add its details to make the identifier unique.

    **Input Data Structure Example:**
    {{
      "tag": "img",
      "alt": "Company Logo",
      "src": "https://example.com/logo.png",
      "id": "main-logo",
      "classes": ["header-logo"],
      "is_likely_logo": true,
      "parent": {{ "tag": "a", "classes": [], "id": "logo-link" }},
      "prev_sibling_text": None,
      "next_sibling_text": "Site Navigation",
      "sequential_index": 0,
      "is_clickable": true,
      "parent_href": "https://example.com/home",
      "uniqueness_context": {{ "level": "id", "value": "main-logo" }} # Optional: Only if needed
    }}

    **Rules for Identifying the Image/Logo in Steps:**
    1. Base Identifier: Prefer `alt` text if descriptive. If not, use the filename part of the `src`. If neither is helpful, use `id` if present.
    2. Construct the base description (e.g., `the image with alt text "Company Logo"`, `the image "logo.png"`, `the image identified by ID "main-logo"`). If `is_likely_logo` is true, prefer descriptions like `the main company logo` if the alt text supports it.
    3. **If `uniqueness_context` exists:** Append the context to the description based on the `level` key:
        - `alt`: Append ` with alt text "VALUE"`
        - `id`: Append ` identified by ID "VALUE"`
        - `src`: Append ` with source "VALUE"` (consider showing just filename)
        - `parent.id`: Append ` within the element with ID "VALUE"`
        - `sibling_text`: Append ` next to the text "VALUE"`
        - `parent_classes`: Append ` within an element with classes "VALUE"`
        - `parent_description`: Append ` within the VALUE`
        - `classes`: Append ` with classes "VALUE"`
    4. Final Identifier String: This combined string (base + context if needed) will be used in the steps.

    **Rules for Step Generation:**
    *   **Visibility Step (Always):** `Then the user should see FINAL_IDENTIFIER_STRING`.
    *   **Remove Redundant Alt Check:** DO NOT generate `And the image should have the alt text ...` step anymore.
    *   **Interaction Steps (Only if `is_clickable` is true):**
        *   `When the user clicks the FINAL_IDENTIFIER_STRING`.
        *   **If `parent_href` exists:** `Then the user should be navigated to the target page with URL "PARENT_HREF_VALUE"`.
        *   **If `parent_href` does NOT exist (or is #):** `Then some action should occur` (or omit if uncertain).

    **Rules for Scenario Title Generation:**
    - Create a user-friendly title reflecting the final unique identification.
    - If `is_clickable` is true, include `interaction` in the title (e.g., "Verify interaction with Company Logo").
    - If `is_clickable` is false, use `visibility` in the title (e.g., "Verify visibility of decorative image header.jpg").
    - Examples: "Verify interaction with Company Logo", "Verify visibility of image product-1.jpg", "Verify interaction with avatar image next to username".
    - Include `Logo` in the title if `is_likely_logo` is true.

    Extracted Images/Logos (Input Data with potential uniqueness_context):
    {json.dumps(image_data, indent=2)}

    Requirements:
    - Generate one `Scenario:` block for EACH item in the input list.
    - Tag appropriately: `@image @visibility`. If `is_clickable` is true, also add `@interaction`. If `is_likely_logo` is true, also add `@logo`.
    - Follow the rules above precisely to determine the Final Identifier String and generate the correct steps based on `is_clickable`.
    - Generate a user-friendly scenario title based on the final identification method and clickability.

    Example Snippets:

      @logo @image @visibility @interaction
      Scenario: Verify interaction with Company Logo with ID main-logo
        Then the user should see the image with alt text "Company Logo" identified by ID "main-logo"
        When the user clicks the image with alt text "Company Logo" identified by ID "main-logo"
        Then the user should be navigated to the target page with URL "https://example.com/home"

      @image @visibility
      Scenario: Verify visibility of product image product-1.jpg
        Then the user should see the image with alt text "Detailed view of Product 1"

      @image @visibility @interaction
      Scenario: Verify interaction with icon image icon-warning.svg next to error message
        Then the user should see the image "icon-warning.svg" next to the text "Error message text..."
        When the user clicks the image "icon-warning.svg" next to the text "Error message text..."
        Then some action should occur
        
    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

def generate_icon_scenarios_prompt(icon_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for icons, using pre-calculated uniqueness context."""
    if not icon_data:
        return ""
    prompt = f"""
    Based on the following icon elements extracted from {url}, generate a Gherkin scenario snippet FOR EACH icon object in the list. Each object includes details like `aria-label`, `title`, `text`, `classes`, parent/sibling info, and potentially a `uniqueness_context` dictionary if needed for disambiguation.

    **Goal:** Generate a clear Scenario and `Then` step for verifying the visibility of each icon. Use the best available identifier (`aria-label`, `title`, `text`, classes) as the base. If `uniqueness_context` is present, add its details to make the step uniquely identifiable.

    **Input Data Structure Example:**
    {{
      "tag": "i",
      "classes": ["fas", "fa-search"],
      "aria_label": "Search",
      "text": null,
      "role": null,
      "parent": {{ "tag": "button", "classes": ["search-btn"], "id": "search-button" }},
      "prev_sibling_text": None,
      "next_sibling_text": "Submit Query",
      "sequential_index": 12,
      "uniqueness_context": null # Optional: Only if needed, e.g., {{ "level": "parent.id", "value": "search-button" }}
    }}

    **Rules for Identifying the Icon in Steps:**
    1. Base Identifier: Prefer `aria-label` if present and descriptive. Otherwise use `title` (for SVGs). Otherwise use `text` content if present (e.g., for Material Icons). As a last resort, describe using classes (e.g., `the 'fas fa-search' icon`).
    2. Construct the base description (e.g., `the icon identified by aria-label "Search"`, `the icon with title "Close button"`, `the icon with text "settings"`, `the 'fas fa-search' icon`).
    3. **If `uniqueness_context` exists:** Append the context to the description based on the `level` key:
        - `aria_label`: Append ` with aria-label "VALUE"`
        - `title`: Append ` with title "VALUE"`
        - `text`: Append ` with text "VALUE"`
        - `parent.id`: Append ` within the element with ID "VALUE"`
        - `sibling_text`: Append ` next to the text "VALUE"`
        - `parent_description`: Append ` within the VALUE`
        - `classes`: Append ` with classes "VALUE"`
    4. Final Identifier String: This combined string (base + context if needed) will be used in the `Then` step.

    **Rules for `Then` (Visibility) Step:**
    - Use the Final Identifier String: `Then the user should see FINAL_IDENTIFIER_STRING`.

    **Rules for Scenario Title Generation:**
    - Create a user-friendly title reflecting the final unique identification.
    - Examples: "Verify visibility of Search icon", "Verify visibility of Close icon within header", "Verify visibility of settings icon next to Account link".
    - Use the identifier determined in step 1 and add context from `uniqueness_context` if used.

    Extracted Icons (Input Data with potential uniqueness_context):
    {json.dumps(icon_data, indent=2)}

    Requirements:
    - Generate one `@icon @visibility` tagged `Scenario:` block for EACH item in the input list.
    - Follow the rules above precisely to determine the Final Identifier String.
    - Generate the `Then` step for visibility verification.
    - Generate a user-friendly scenario title based on the final identification method.

    Example Snippets:

      @icon @visibility
      Scenario: Verify visibility of Search icon
        # Base identifier: aria-label = "Search" (assumed unique)
        Then the user should see the icon identified by aria-label "Search"
        
      @icon @visibility
      Scenario: Verify visibility of Settings icon next to Account Settings text
        # Base identifier: aria-label = "Settings Gear" (assumed duplicate)
        # uniqueness_context: {{ "level": "sibling_text", "value": "Account Settings" }}
        Then the user should see the icon with aria-label "Settings Gear" next to the text "Account Settings"
        
      @icon @visibility
      Scenario: Verify visibility of Edit icon within element ID user-profile-actions
        # Base identifier: aria-label = "Edit" (assumed duplicate)
        # uniqueness_context: {{ "level": "parent.id", "value": "user-profile-actions" }}
        Then the user should see the icon with aria-label "Edit" within the element with ID "user-profile-actions"

      @icon @visibility
      Scenario: Verify visibility of info icon with classes "icon icon-info-circle blue"
        # Base identifier: classes = "icon icon-info-circle blue" (assumed unique enough or other IDs failed)
        Then the user should see the icon with classes "icon icon-info-circle blue"

    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

def generate_link_scenarios_prompt(link_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for links, using DOM context."""
    if not link_data:
        return ""
    
    # Extract base domain from the input URL
    parsed_url = urlparse(url)
    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    prompt = f"""
    Based on the following link elements extracted from {url}, generate comprehensive Gherkin scenario snippets for each link. Each object includes complete DOM context that shows the link's position in the page structure, including parent elements, ancestors, siblings, and any interactive elements that need to be interacted with before reaching the link.

    **Goal:** Analyze the DOM context for each link and generate scenarios that include ALL necessary steps to interact with the link, focusing on core website elements and navigation. Scenarios should NOT be generated for interactions with cookie consent banners or other general overlay popups unless they are a direct pre-requisite for accessing a primary site element.

    **Important URL Handling:**
    - Base domain for this page: {base_domain}
    - For relative URLs (starting with /), prepend the base domain
    - For absolute URLs (starting with http:// or https://), use as is
    - For external links, use the complete URL including protocol and domain

    **Input Data Structure Example:**
    {{
        "dom_context": {{
            "element": {{
                "tag": "a",
                "attributes": {{"href": "/path", "class": "nav-link"}},
                "classes": ["nav-link"],
                "id": "link-1",
                "aria_label": "Example Link",
                "text": "Example",
                "href": "/path"
            }},
            "parent": {{
                "tag": "li",
                "attributes": {{"class": "nav-item"}},
                "classes": ["nav-item"],
                "role": "menuitem"
            }},
            "ancestors": [
                {{
                    "tag": "ul",
                    "attributes": {{"class": "nav-menu"}},
                    "classes": ["nav-menu"],
                    "role": "menu"
                }},
                {{
                    "tag": "nav",
                    "attributes": {{"class": "main-nav"}},
                    "classes": ["main-nav"],
                    "role": "navigation"
                }}
            ],
            "siblings": {{
                "previous": [],
                "next": []
            }},
            "children": [],
            "interactive_parents": [
                {{
                    "tag": "button",
                    "attributes": {{"class": "menu-toggle"}},
                    "classes": ["menu-toggle"],
                    "role": "button",
                    "aria_expanded": "false",
                    "aria_controls": "nav-menu"
                }}
            ]
        }},
        "is_external_link": false,
        "external_link_popup": false
    }}

    **Rules for Scenario Generation:**

    1. **Analyze DOM Context:**
       - Check for interactive parents (buttons, links, etc.) that need to be clicked first.
       - Look for parent elements with roles like 'menu', 'tablist', 'accordion'.
       - Identify any elements with aria-expanded that need to be expanded.
       - Note any aria-controls relationships that indicate parent-child interactions.
       - Check for any required scrolling or viewport adjustments.
       - **IGNORE elements primarily related to cookie consent banners or general overlay popups (e.g., GDPR notices, newsletter signups not part of a primary user flow). Do not generate dedicated scenarios for these elements.**

    2. **Generate Steps in Order:**
       - Start with any required parent interactions (e.g., clicking menu buttons).
       - Include steps for expanding/collapsing containers.
       - Add steps for navigating through menus/dropdowns.
       - Add steps for scrolling if needed.
       - End with the actual link interaction.

    3. **Common Patterns to Handle (for main website elements):**
       - Main Menu Navigation:
         ```gherkin
         Given the user is on the homepage
         When the user clicks the menu icon
         Then the main menu should be visible
         When the user clicks the "[Menu Item]" link in the main menu
         Then the submenu should be visible
         Then the user should see the "[Link Text]" link
         When the user clicks the "[Link Text]" link
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Dropdown Menu Navigation (Click-based):
         ```gherkin
         Given the user is on the homepage
         When the user clicks the "[Menu Item]" link
         Then the dropdown menu should be visible
         Then the user should see the "[Link Text]" link in the dropdown
         When the user clicks the "[Link Text]" link in the dropdown
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Dropdown Menu Navigation (Hover-based):
         ```gherkin
         Given the user is on the homepage
         When the user hovers over the "[Menu Item]" link
         Then the dropdown menu should be visible
         Then the user should see the "[Link Text]" link in the dropdown
         When the user clicks the "[Link Text]" link in the dropdown
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Header Navigation (Click-based):
         ```gherkin
         Given the user is on the homepage
         When the user clicks the "[Menu Item]" link in the header
         Then the dropdown menu should be visible
         Then the user should see the "[Link Text]" link in the dropdown
         When the user clicks the "[Link Text]" link in the dropdown
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Header Navigation (Hover-based):
         ```gherkin
         Given the user is on the homepage
         When the user hovers over the "[Menu Item]" link in the header
         Then the dropdown menu should be visible
         Then the user should see the "[Link Text]" link in the dropdown
         When the user clicks the "[Link Text]" link in the dropdown
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Accordion Navigation:
         ```gherkin
         Then the user should see the accordion header
         When the user clicks the accordion header
         Then the accordion content should be expanded
         Then the user should see the "[Link Text]" link
         When the user clicks the "[Link Text]" link
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Tab Navigation:
         ```gherkin
         Then the user should see the "[Tab Name]" tab
         When the user clicks the "[Tab Name]" tab
         Then the tab content should be visible
         Then the user should see the "[Link Text]" link
         When the user clicks the "[Link Text]" link
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Breadcrumb Navigation:
         ```gherkin
         Then the user should see the breadcrumb navigation
         Then the user should see the "[Link Text]" link in the breadcrumb
         When the user clicks the "[Link Text]" link in the breadcrumb
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Pagination Navigation:
         ```gherkin
         Then the user should see the pagination controls
         Then the user should see the "[Link Text]" link in the pagination
         When the user clicks the "[Link Text]" link in the pagination
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Footer Link:
         ```gherkin
         Then the user should see the footer section
         Then the user should see the "[Link Text]" link in the footer
         When the user clicks the "[Link Text]" link in the footer
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Sidebar Link:
         ```gherkin
         Then the user should see the sidebar
         Then the user should see the "[Link Text]" link in the sidebar
         When the user clicks the "[Link Text]" link in the sidebar
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

       - Social Media Link:
         ```gherkin
         Then the user should see the social media section
         Then the user should see the "[Link Text]" social media link
         When the user clicks the "[Link Text]" social media link
         Then the user should be navigated to the target page with URL "https://external-domain.com/[path]"
         ```

       - Action Link:
         ```gherkin
         Then the user should see the "[Link Text]" action link
         When the user clicks the "[Link Text]" action link
         Then the user should be navigated to the target page with URL "{base_domain}/[path]"
         ```

    **Rules for URL Handling in Navigation Steps:**
    1. For relative URLs (starting with /):
       - Prepend the base domain: `{base_domain}/[path]`
    2. For absolute URLs (starting with http:// or https://):
       - Use the complete URL as is
    3. For external links:
       - Use the complete URL including protocol and domain
    4. For anchor links (starting with #):
       - Use the current page URL with the anchor: `{base_domain}/current-path#[anchor]`

    **Rules for Link Identification:**
    1. Use the most specific identifier available in this order:
       - ID if present
       - aria-label if present
       - text content
       - parent context (e.g., "in the navigation", "in the accordion")
    2. Add context from DOM structure to make the identification unique
    3. Use parent/sibling information to create meaningful scenario titles

    **Rules for Scenario Titles:**
    - Include the complete path to the link (e.g., "in Main Menu > Products > View Details")
    - Mention any special containers (e.g., "in accordion", "in dropdown")
    - For external links, mention "external" in the title
    - For social media links, mention the platform (e.g., "Facebook", "Twitter")
    - For action links, mention the action type (e.g., "Read More", "Learn More")

    **Rules for Menu Interaction:**
    1. For click-based menus:
       - Use "clicks" instead of "hovers" for menu interaction
       - Verify menu visibility after clicking
       - Include steps to verify submenu/dropdown visibility
    2. For hover-based menus:
       - Use "hovers over" for menu interaction
       - Verify menu visibility after hovering
       - Include steps to verify submenu/dropdown visibility
    3. For both types:
       - Always verify the menu/dropdown is visible before proceeding
       - Include context in link identification (e.g., "in the dropdown")
       - Use appropriate tags (@click-menu or @hover-menu)

    Extracted Links (Input Data):
    {json.dumps(link_data, indent=2)}

    Requirements:
    - Generate one `@link @visibility @interaction` tagged `Scenario:` block for EACH item in the input list that is part of the main website content and functionality.
    - **Do NOT generate scenarios for cookie consent banners, GDPR notices, or similar general overlay popups.**
    - Analyze the DOM context to determine all required interactions for core website elements.
    - Include ALL necessary steps to reach and interact with the link.
    - Generate clear and descriptive scenario titles that reflect the complete path.
    - Always use complete URLs in navigation verification steps.
    - Add appropriate tags based on link type (e.g., @menu, @accordion, @dropdown, @tab, @breadcrumb, @pagination, @footer, @header, @sidebar, @social, @action).
    - For menu items, ensure proper hover/click interactions based on the menu type.
    - For dropdown items, include steps to verify the dropdown is visible before clicking the link.
    - Add @click-menu or @hover-menu tag based on the interaction type.

    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

# --- New Prompt for Buttons ---
def generate_button_scenarios_prompt(button_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for buttons, using pre-calculated uniqueness context."""
    if not button_data:
        return ""
    prompt = f"""
    Based on the following button elements extracted from {url}, generate a Gherkin scenario snippet FOR EACH button object in the list. Each object includes `text` (or value/aria-label), `id`, `name`, `type`, `classes`, parent/sibling info, and potentially a `uniqueness_context` dictionary.

    **Goal:** Generate a clear Scenario, `Then` step for visibility, and `When` step for interaction for each button. Use the best available identifier (`id`, `text`, `name`, `type`) as the base. If `uniqueness_context` is present, add its details to make the step uniquely identifiable.

    **Input Data Structure Example:**
    {{
      "tag": "button",
      "type": "submit",
      "text": "Login",
      "id": "login-button",
      "name": "login",
      "classes": ["btn", "btn-primary"],
      "contains_icon": false,
      "parent": {{ "tag": "form", "classes": [], "id": "login-form" }},
      "prev_sibling_text": "Password",
      "next_sibling_text": None,
      "sequential_index": 2,
      "uniqueness_context": null # Optional: Only if needed
    }}

    **Rules for Identifying the Button in Steps:**
    1. Base Identifier: Prefer `id` if present. Otherwise use `text` (which might be value or aria-label). Otherwise use `name` attribute. If all else fails, use the `type` (e.g., "the submit button").
    2. Construct the base description (e.g., `the button identified by ID "login-button"`, `the "Login" button`, `the button named "login"`, `the submit button`).
    3. **If `uniqueness_context` exists:** Append the context to the description based on the `level` key:
        - `id`: Append ` identified by ID "VALUE"`
        - `text`: Append ` with text "VALUE"`
        - `name`: Append ` named "VALUE"`
        - `type`: Append ` of type "VALUE"`
        - `parent.id`: Append ` within the element with ID "VALUE"`
        - `sibling_text`: Append ` next to the text "VALUE"`
        - `parent_classes`: Append ` within an element with classes "VALUE"`
        - `parent_description`: Append ` within the VALUE`
        - `classes`: Append ` with classes "VALUE"`
    4. Final Identifier String: This combined string (base + context if needed) will be used in `Then` and `When` steps.

    **Rules for `Then` (Visibility) Step:**
    - Use the Final Identifier String: `Then the user should see FINAL_IDENTIFIER_STRING`.

    **Rules for `When` (Interaction) Step:**
    - Use the Final Identifier String: `When the user clicks the FINAL_IDENTIFIER_STRING`.
    - Optional: Add a `Then` step for expected outcome if obvious, otherwise leave it open.

    **Rules for Scenario Title Generation:**
    - Create a user-friendly title reflecting the final unique identification.
    - Examples: "Verify interaction with Login button", "Verify interaction with submit button within login-form", "Verify visibility of Cancel button next to Submit".
    - Use the identifier determined in step 1 and add context from `uniqueness_context` if used.

    Extracted Buttons (Input Data with potential uniqueness_context):
    {json.dumps(button_data, indent=2)}

    Requirements:
    - Generate one `@button @visibility @interaction` tagged `Scenario:` block for EACH item in the input list.
    - Follow the rules above precisely to determine the Final Identifier String.
    - Generate the `Then` (visibility) and `When` (click) steps.
    - Generate a user-friendly scenario title based on the final identification method.

    Example Snippets:

      @button @visibility @interaction
      Scenario: Verify interaction with Login button with ID login-button
        # Base identifier: id = "login-button" (assumed unique)
        Then the user should see the button identified by ID "login-button"
        When the user clicks the button identified by ID "login-button"

      @button @visibility @interaction
      Scenario: Verify interaction with Submit button within element ID search-form
        # Base identifier: type = "submit" (assumed duplicate)
        # uniqueness_context: {{ "level": "parent.id", "value": "search-form" }}
        Then the user should see the submit button within the element with ID "search-form"
        When the user clicks the submit button within the element with ID "search-form"

      @button @visibility @interaction
      Scenario: Verify interaction with "Add to Cart" button next to product title
        # Base identifier: text = "Add to Cart" (assumed duplicate)
        # uniqueness_context: {{ "level": "sibling_text", "value": "Product Title XYZ" }}
        Then the user should see the "Add to Cart" button next to the text "Product Title XYZ"
        When the user clicks the "Add to Cart" button next to the text "Product Title XYZ"

    Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background.
    """
    return prompt

# Add the new function here
def generate_form_scenarios_prompt(form_data: List[Dict], url: str) -> str:
    """Generate prompt for Gherkin scenario snippets for form submissions."""
    if not form_data:
        return ""
    prompt = f"""
    Based on the following form structures extracted from {url}, generate one detailed Gherkin scenario snippet FOR EACH form object in the list. Each object describes a form, its input fields (including type, identifier, and required status), and its submit button.

    **Goal:** Generate a clear, actionable Gherkin Scenario for a positive path test case (submitting with valid data in required fields). Describe the interaction field-by-field, followed by the submission action and expected success outcome. Use specific input type descriptions (e.g., "valid email address", "valid name") based on field details. An AI browser agent will execute these steps.

    **Input Data Structure Example (One Form):**
    {{
      "form_identifier": "the 'Sign Up Now' form",
      "inputs": [
        {{ "identifier": "'First name' field", "tag": "input", "type": "text", "required": true }},
        {{ "identifier": "'Last name' field", "tag": "input", "type": "text", "required": true }},
        {{ "identifier": "'Email address' field", "tag": "input", "type": "email", "required": true }},
        {{ "identifier": "'Area of Interest' dropdown", "tag": "select", "type": "select", "required": false }}
      ],
      "submit_button": {{ "text": "Sign up", "identifier": "the 'Sign up' button" }}
    }}

    **Rules for Scenario Generation (Positive Path):**
    1. **Scenario Title:** 
       - For login forms: "User logs in with valid credentials"
       - For other forms: "User submits the FORM_IDENTIFIER with valid required details". 
       - Infer the form purpose if possible from the identifier.
       
    2. **`Given` Step:** DO NOT generate a Given step here. It should be handled by a Background step externally (e.g., "Given the user navigates to the page").
    
    3. **Interaction Steps (Field by Field):**
       - **For login forms:**
         - For username/email fields: `When the user enters a valid username in the USERNAME_FIELD`
         - For password fields: `And the user enters a valid password in the PASSWORD_FIELD`
         - Special handling for "remember me" or similar checkboxes: `And the user checks the "Remember me" checkbox` (only if present)
       
       - **For other forms:**
         - For the *first required* input field: Start with `When the user enters/selects/interacts with...` using a specific action based on the input type and a description of the data (e.g., `a valid first name`, `a valid email address`, `an option`). Specify the field using its `identifier`. Indicate if it's required (e.g., `in the required 'First name' field`).
         - For *each subsequent* input field (both required and potentially optional ones for a thorough positive test): Add `And the user enters/selects/interacts with...` similarly, using specific data descriptions and the field identifier.
       
       - **Action Phrasing:** 
         - Use "enters a valid username" for username fields in login forms
         - Use "enters a valid password" for password fields in login forms
         - Use "enters a valid [data type] in..." for text inputs (text, email, password, etc.) in other forms
         - Use "selects a valid option from..." for select dropdowns
         - Use "interacts with..." for checkboxes, radio buttons
         - Infer [data type] from field name/identifier (e.g., 'email address' -> 'email address', 'First name' -> 'first name')
    
    4. **Click Step:** After iterating through inputs: `And clicks the SUBMIT_BUTTON_IDENTIFIER`. Use `submit_button.identifier`.
    
    5. **Outcome Steps (`Then`):** 
       - For login forms: `Then the user should be successfully logged in`
       - For other forms: 
         - `Then the form should be submitted successfully`
         - `And the user should see a success indication` (e.g., confirmation message, navigation)
    
    6. **Tags:** 
       - For login forms: Add `@login @authentication @positive` tags
       - For other forms: Add `@form @interaction @positive` tags

    **Special Handling for Login Forms:**
    - If a form contains username/email field and password field, treat it as a login form
    - If a form has "login" or similar terms in its identifier, treat it as a login form
    - Use simpler, more direct steps for login forms
    - Login forms should have different outcome steps and tags

    Extracted Forms (Input Data - includes 'required' flag):
    {json.dumps(form_data, indent=2)}

    Requirements:
    - Generate one properly tagged `Scenario:` block for EACH form item in the input list
    - Follow the rules above precisely to create the Scenario title and the sequence of specific `When`/`And`/`Then` steps for a positive submission path
    - Treat login forms differently as specified in the rules
    - Generate specific interaction steps based on input `type` and `identifier`
    - Generate specific, positive outcome `Then` steps
    - Generate ONLY the Gherkin scenario snippets (tags and Scenario blocks). Do NOT include Feature or Background

    Example Snippets:

      # Example 1: Login Form
      @login @authentication @positive
      Scenario: User logs in with valid credentials
        When the user enters a valid username in the 'Username' field
        And the user enters a valid password in the 'Password' field
        And clicks the 'Login' button
        Then the user should be successfully logged in
      
      # Example 2: Sign Up Form  
      @form @interaction @positive
      Scenario: User submits the 'Sign Up Now' form with valid required details
        When the user enters a valid first name in the required 'First name' field
        And the user enters a valid last name in the required 'Last name' field
        And the user enters a valid email address in the required 'Email address' field
        And the user selects a valid option from the 'Area of Interest' dropdown
        And clicks the 'Sign up' button
        Then the form should be submitted successfully
        And the user should see a success indication

      # Example 3: Simple Search Form
      @form @interaction @positive
      Scenario: User submits the Search form with valid required details
        When the user enters a valid search term in the required field labelled 'Search query'
        And clicks the 'Search' button with ID 'search-submit'
        Then the form should be submitted successfully
        And the user should see a success indication

    # --- Note on Input Step Phrasing --- 
    # Use "enters a valid username" for username fields in login forms
    # Use "enters a valid password" for password fields in login forms
    # Use "enters a valid [data type] in..." for text-like inputs (text, password, email, textarea, etc.)
    # Use "selects a valid option from..." for dropdowns (select)
    # Use "interacts with..." for checkboxes, radio buttons
    # Infer [data type] from field name/identifier/type (e.g., 'email address' -> 'email address', 'First name' -> 'first name')
    # Indicate if a field is required based on the `required` flag in the input data.

    """
    return prompt