from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, Any, List

# --- Functions for URL-based Scenario Generation ---

async def fetch_html_content(url: str) -> str:
    """Fetch the HTML content of a given URL using Playwright."""
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")
            # Optional: Add a small delay or wait for a specific element if needed
            await page.wait_for_timeout(7000) # Wait 7 seconds 
            html_content = await page.content()
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            html_content = f"Error fetching URL: {str(e)}"
        finally:
            await browser.close()
    return html_content

def parse_menu_structure(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Parse the HTML to extract menu structure including multi-level menus."""
    menus = []
    
    # Find all menu containers
    menu_containers = soup.find_all(class_=lambda x: x and 'menu' in x)
    
    for container in menu_containers:
        menu_data = {
            "level": 1 if 'level1' in container.get('class', []) else 2,
            "title": None,
            "menu_items": []
        }
        
        # Get menu title
        title_elem = container.find('h2')
        if title_elem:
            menu_data["title"] = title_elem.get_text(strip=True)
            
        # Get menu items
        for li in container.find_all('li'):
            item = {
                "text": None,
                "href": None,
                "has_submenu": False,
                "submenu": None
            }
            
            # Get link element
            link = li.find('a')
            if link:
                item["text"] = link.get_text(strip=True)
                item["href"] = link.get('href', '#')
                
                # Check if this item has a submenu
                if 'nav-sub-menu' in li.get('class', []):
                    item["has_submenu"] = True
                    # Find the corresponding submenu
                    submenu_class = f"sub-menu-{item['text'].lower().replace(' ', '-')}"
                    submenu = soup.find(class_=lambda x: x and submenu_class in x)
                    if submenu:
                        item["submenu"] = parse_menu_structure(submenu)
            
            if item["text"]:  # Only add items with text
                menu_data["menu_items"].append(item)
                
        menus.append(menu_data)
    
    return menus

def parse_html_for_elements(html_content: str, base_url: str, max_elements: int = 5000) -> Dict[str, List[Dict[str, Any]]]:
    """Parse HTML to extract key elements relevant for test scenario generation."""
    if html_content.startswith("Error fetching URL"):
        return {"error": html_content}
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, and potentially header/footer if focusing only on main content?
    # For now, keep header/footer to find logos etc.
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
        
    elements = {
        "headings": [],
        "paragraphs": [],
        "links": [],
        "buttons": [],
        "inputs": [],
        "images_and_logos": [],
        "icons": [],
        "forms": [],
        "semantic_elements": []
    }
    
    # Initialize element count and seen links set
    element_count = 0
    seen_links = set()
    
    # Define common icon classes (extend this list as needed)
    icon_classes = ["fa", "fas", "far", "fal", "fab", "glyphicon", "material-icons"]
    
    # Define semantic tags to look for
    semantic_tags = ["header", "footer", "nav", "main", "section", "article", "aside"]

    # Collect heading data
    heading_index = 0
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7']):
        if element_count >= max_elements: break
        
        text = heading.get_text(strip=True)
        if text:  # Only process headings with text
            # Capture complete DOM context
            dom_context = {
                "element": {
                    "tag": heading.name,
                    "attributes": dict(heading.attrs),
                    "classes": heading.get('class', []),
                    "id": heading.get('id'),
                    "aria_label": heading.get('aria-label'),
                    "text": text,
                    "role": heading.get('role')
                },
                "parent": None,
                "ancestors": [],
                "siblings": {
                    "previous": [],
                    "next": []
                },
                "children": [],
                "interactive_parents": []
            }
            
            # Capture parent and ancestors
            current = heading.parent
            while current and current.name:
                parent_info = {
                    "tag": current.name,
                    "attributes": dict(current.attrs),
                    "classes": current.get('class', []),
                    "id": current.get('id'),
                    "aria_label": current.get('aria-label'),
                    "role": current.get('role'),
                    "aria_expanded": current.get('aria-expanded'),
                    "aria_controls": current.get('aria-controls'),
                    "aria_labelledby": current.get('aria-labelledby')
                }
                
                if current == heading.parent:
                    dom_context["parent"] = parent_info
                else:
                    dom_context["ancestors"].append(parent_info)
                
                # Check if parent is interactive
                if current.name in ['button', 'a'] or current.get('role') in ['button', 'tab', 'menuitem']:
                    dom_context["interactive_parents"].append(parent_info)
                
                current = current.parent
            
            # Capture siblings
            prev_sibling = heading.find_previous_sibling()
            while prev_sibling and len(dom_context["siblings"]["previous"]) < 3:
                if prev_sibling.name:
                    sibling_info = {
                        "tag": prev_sibling.name,
                        "attributes": dict(prev_sibling.attrs),
                        "classes": prev_sibling.get('class', []),
                        "id": prev_sibling.get('id'),
                        "text": prev_sibling.get_text(strip=True),
                        "role": prev_sibling.get('role')
                    }
                    dom_context["siblings"]["previous"].append(sibling_info)
                prev_sibling = prev_sibling.find_previous_sibling()
            
            next_sibling = heading.find_next_sibling()
            while next_sibling and len(dom_context["siblings"]["next"]) < 3:
                if next_sibling.name:
                    sibling_info = {
                        "tag": next_sibling.name,
                        "attributes": dict(next_sibling.attrs),
                        "classes": next_sibling.get('class', []),
                        "id": next_sibling.get('id'),
                        "text": next_sibling.get_text(strip=True),
                        "role": next_sibling.get('role')
                    }
                    dom_context["siblings"]["next"].append(sibling_info)
                next_sibling = next_sibling.find_next_sibling()
            
            # Capture children
            for child in heading.find_all(recursive=False):
                child_info = {
                    "tag": child.name,
                    "attributes": dict(child.attrs),
                    "classes": child.get('class', []),
                    "id": child.get('id'),
                    "text": child.get_text(strip=True),
                    "role": child.get('role')
                }
                dom_context["children"].append(child_info)
            
            # Add to elements list
            elements["headings"].append({
                "dom_context": dom_context,
                "sequential_index": heading_index
            })
            
            heading_index += 1
            element_count += 1

    # Paragraphs (p)
    paragraph_index = 0 # Initialize paragraph index
    for p in soup.find_all("p"):
        if element_count >= max_elements: break
        text = p.get_text(strip=True)
        
        # Check if the paragraph is directly inside a link or button element
        is_part_of_interactive = False
        if p.parent:
            # Ensure parent.name is not None before lowercasing
            parent_tag = p.parent.name.lower() if p.parent.name else ""
            parent_role = p.parent.get("role", "").lower()
            if parent_tag in ['a', 'button'] or parent_role == 'button':
                is_part_of_interactive = True
        
        if is_part_of_interactive:
            continue # Skip this paragraph, it's part of a link/button
        
        # Check if the paragraph *only* contains a heading or other element handled elsewhere
        significant_children = [child for child in p.children if not (isinstance(child, str) and child.strip() == "")]
        if len(significant_children) == 1:
            child = significant_children[0]
            # Check if the single child is a heading, ensuring child.name is not None
            if hasattr(child, 'name') and child.name and child.name.lower() in [f'h{i}' for i in range(1, 7)]:
                 continue # Skip this paragraph, its content is just a heading handled elsewhere
        
        # Add only if paragraph has substantial text, is not part of a link/button, and doesn't solely contain a heading
        if text and len(text) > 10: 
            # Context capture similar to icons
            parent_info = None
            if p.parent:
                parent_info = {
                    "tag": p.parent.name, 
                    "classes": p.parent.get('class', []),
                    "id": p.parent.get('id') 
                }
                
            # --- Enhanced Sibling Text Logic --- 
            prev_sibling_text = None
            # Try immediate previous text sibling
            prev_node = p.previous_sibling
            if prev_node and isinstance(prev_node, str) and prev_node.strip():
                prev_sibling_text = prev_node.strip()
            # If not found, try nearest previous *element* sibling's text
            elif not prev_sibling_text:
                prev_elem_sibling = p.find_previous_sibling()
                if prev_elem_sibling:
                    prev_sibling_text = prev_elem_sibling.get_text(strip=True)
                    
            next_sibling_text = None
            # Try immediate next text sibling
            next_node = p.next_sibling
            if next_node and isinstance(next_node, str) and next_node.strip():
                next_sibling_text = next_node.strip()
            # If not found, try nearest next *element* sibling's text
            elif not next_sibling_text:
                next_elem_sibling = p.find_next_sibling()
                if next_elem_sibling:
                    next_sibling_text = next_elem_sibling.get_text(strip=True)
            # --- End Enhanced Sibling Text Logic ---

            elements["paragraphs"].append({
                "tag": p.name, 
                "text_snippet": text[:100] + ("..." if len(text) > 100 else ""), # Store snippet
                "id": p.get("id"), # Get paragraph's own ID
                "classes": p.get("class", []), # Get paragraph's own classes
                "parent": parent_info,
                "prev_sibling_text": prev_sibling_text, # Use enhanced value
                "next_sibling_text": next_sibling_text, # Use enhanced value
                "sequential_index": paragraph_index
            }) 
            paragraph_index += 1
            element_count += 1
            
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v}

    # --- Menu Icon Logic ---
    # Find menu icon first
    menu_icon = soup.find(class_=lambda x: x and 'menu-icon' in x)
    menu_icon_id = menu_icon.get('id') if menu_icon else None

    # --- Menu Button Logic ---
    # First, identify all menu buttons (links that lead to submenus)
    menu_buttons = {}
    for a in soup.find_all("a", href=True):
        if 'nav-sub-menu' in a.parent.get('class', []):
            menu_buttons[a.get_text(strip=True)] = {
                "id": a.get('id'),
                "href": a.get('href'),
                "text": a.get_text(strip=True)
            }
    
    # Links (a)
    link_index = 0
    for a in soup.find_all("a", href=True):
        if element_count >= max_elements: break
        href = a['href']
        text = a.get_text(strip=True)
        link_id = a.get('id')
        aria_label = a.get('aria-label')
        
        # Capture complete DOM context
        dom_context = {
            "element": {
                "tag": a.name,
                "attributes": dict(a.attrs),
                "classes": a.get('class', []),
                "id": link_id,
                "aria_label": aria_label,
                "text": text,
                "href": href
            },
            "parent": None,
            "ancestors": [],
            "siblings": {
                "previous": [],
                "next": []
            },
            "children": [],
            "interactive_parents": []
        }
        
        # Capture parent and ancestors
        current = a.parent
        while current and current.name:
            parent_info = {
                "tag": current.name,
                "attributes": dict(current.attrs),
                "classes": current.get('class', []),
                "id": current.get('id'),
                "aria_label": current.get('aria-label'),
                "role": current.get('role'),
                "aria_expanded": current.get('aria-expanded'),
                "aria_controls": current.get('aria-controls'),
                "aria_labelledby": current.get('aria-labelledby')
            }
            
            if current == a.parent:
                dom_context["parent"] = parent_info
            else:
                dom_context["ancestors"].append(parent_info)
            
            # Check if parent is interactive
            if current.name in ['button', 'a'] or current.get('role') in ['button', 'tab', 'menuitem']:
                dom_context["interactive_parents"].append(parent_info)
            
            current = current.parent
        
        # Capture siblings
        prev_sibling = a.find_previous_sibling()
        while prev_sibling and len(dom_context["siblings"]["previous"]) < 3:
            if prev_sibling.name:
                sibling_info = {
                    "tag": prev_sibling.name,
                    "attributes": dict(prev_sibling.attrs),
                    "classes": prev_sibling.get('class', []),
                    "id": prev_sibling.get('id'),
                    "text": prev_sibling.get_text(strip=True),
                    "role": prev_sibling.get('role')
                }
                dom_context["siblings"]["previous"].append(sibling_info)
            prev_sibling = prev_sibling.find_previous_sibling()
        
        next_sibling = a.find_next_sibling()
        while next_sibling and len(dom_context["siblings"]["next"]) < 3:
            if next_sibling.name:
                sibling_info = {
                    "tag": next_sibling.name,
                    "attributes": dict(next_sibling.attrs),
                    "classes": next_sibling.get('class', []),
                    "id": next_sibling.get('id'),
                    "text": next_sibling.get_text(strip=True),
                    "role": next_sibling.get('role')
                }
                dom_context["siblings"]["next"].append(sibling_info)
            next_sibling = next_sibling.find_next_sibling()
        
        # Capture children
        for child in a.find_all(recursive=False):
            child_info = {
                "tag": child.name,
                "attributes": dict(child.attrs),
                "classes": child.get('class', []),
                "id": child.get('id'),
                "text": child.get_text(strip=True),
                "role": child.get('role')
            }
            dom_context["children"].append(child_info)
        
        # Add to elements list
        elements["links"].append({
            "dom_context": dom_context,
            "is_external_link": 'data-external-link-popup' in a.attrs,
            "external_link_popup": 'data-external-link-popup' in a.attrs and 'data-external-skipped-whitelisted' not in a.attrs
        })
        
        element_count += 1
            
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v}

    # Buttons (button, input[type=button/submit/reset], role=button)
    button_index = 0 # Add index
    for btn in soup.find_all(["button", lambda tag: tag.name == "input" and tag.get("type") in ["button", "submit", "reset"], lambda tag: tag.get("role") == "button"]):
        if element_count >= max_elements: break
        
        # *** ADDED: Skip buttons inside forms, they will be handled by form logic ***
        if btn.form:
            continue
            
        text = btn.get_text(strip=True) or btn.get("value", "") or btn.get("aria-label", "")
        btn_id = btn.get('id') # Get button ID
        btn_type = btn.get("type", "button") # Get type (esp. for input)
        btn_name = btn.get("name") # Get name attribute
        
        # Context capture
        parent_info = None
        if btn.parent:
            parent_info = {
                "tag": btn.parent.name, 
                "classes": btn.parent.get('class', []),
                "id": btn.parent.get('id') 
            }
        prev_sibling_text = None
        prev_node = btn.previous_sibling
        if prev_node and isinstance(prev_node, str) and prev_node.strip():
             prev_sibling_text = prev_node.strip()
        elif not prev_sibling_text:
             prev_elem_sibling = btn.find_previous_sibling()
             if prev_elem_sibling: prev_sibling_text = prev_elem_sibling.get_text(strip=True)
             
        next_sibling_text = None
        next_node = btn.next_sibling
        if next_node and isinstance(next_node, str) and next_node.strip():
             next_sibling_text = next_node.strip()
        elif not next_sibling_text:
             next_elem_sibling = btn.find_next_sibling()
             if next_elem_sibling: next_sibling_text = next_elem_sibling.get_text(strip=True)

        contains_icon = any(child.name in ["i", "span", "svg"] for child in btn.children if hasattr(child, "name"))
        
        # Require text or potential icon to consider it a valid button for testing
        if text or contains_icon: 
            elements["buttons"].append({
                "tag": btn.name, 
                "type": btn_type, 
                "text": text, 
                "id": btn_id, # Add ID
                "name": btn_name, # Add name
                "classes": btn.get('class', []), # Add classes
                "contains_icon": contains_icon,
                "parent": parent_info, # Add parent info
                "prev_sibling_text": prev_sibling_text, # Add sibling text
                "next_sibling_text": next_sibling_text, # Add sibling text
                "sequential_index": button_index # Add index
            })
            button_index += 1
            element_count += 1
            
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v}

    # Images and Logos (img)
    image_index = 0 # Add index
    for img in soup.find_all("img"):
        if element_count >= max_elements: break
        alt_text = img.get("alt", "")
        src = img.get("src", "")
        # Context capture
        parent_info = None
        if img.parent:
            parent_info = {
                "tag": img.parent.name, 
                "classes": img.parent.get('class', []),
                "id": img.parent.get('id') 
            }
        prev_sibling_text = None
        prev_node = img.previous_sibling
        if prev_node and isinstance(prev_node, str) and prev_node.strip():
             prev_sibling_text = prev_node.strip()
        elif not prev_sibling_text:
             prev_elem_sibling = img.find_previous_sibling()
             if prev_elem_sibling: prev_sibling_text = prev_elem_sibling.get_text(strip=True)
             
        next_sibling_text = None
        next_node = img.next_sibling
        if next_node and isinstance(next_node, str) and next_node.strip():
             next_sibling_text = next_node.strip()
        elif not next_sibling_text:
             next_elem_sibling = img.find_next_sibling()
             if next_elem_sibling: next_sibling_text = next_elem_sibling.get_text(strip=True)

        # Basic check if src exists, alt text is optional but good for identification
        if src:
            # Determine if the image or its parent is clickable (link)
            is_clickable = False
            parent_href = None
            if img.parent and img.parent.name == 'a':
                is_clickable = True
                parent_href = img.parent.get('href')
                if parent_href: # Resolve relative URLs
                   parent_href = urljoin(base_url, parent_href)
            
            is_logo = "logo" in alt_text.lower() or any(parent.name == "header" for parent in img.parents)
            absolute_src = urljoin(base_url, src)
            elements["images_and_logos"].append({
                "tag": img.name, 
                "alt": alt_text, 
                "src": absolute_src, # Use absolute src
                "id": img.get('id'), # Add ID
                "classes": img.get('class', []), # Add classes
                "is_likely_logo": is_logo,
                "parent": parent_info, # Add parent info
                "prev_sibling_text": prev_sibling_text, # Add sibling text
                "next_sibling_text": next_sibling_text, # Add sibling text
                "sequential_index": image_index, # Add index
                "is_clickable": is_clickable, # Add clickability flag
                "parent_href": parent_href # Add parent href if applicable
            })
            image_index += 1
            element_count += 1
            
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v}
    
    # Icons (i, span with icon classes, svg)
    icon_index = 0 
    for tag in soup.find_all(["i", "span"]):
        if element_count >= max_elements: break 
            
        tag_classes = tag.get('class', [])
        aria_label = tag.get('aria-label')
        icon_text = tag.get_text(strip=True)
        role = tag.get('role')
        has_icon_or_logo_in_class = any("icon" in cls or "logo" in cls for cls in tag_classes)
        is_empty_or_nested_only = not icon_text and all(not isinstance(child, str) or child.strip() == "" for child in tag.contents)
        
        # Context capture - Adding parent ID
        parent_info = None
        if tag.parent:
            parent_info = {
                "tag": tag.parent.name, 
                "classes": tag.parent.get('class', []),
                "id": tag.parent.get('id') 
            }
        prev_sibling = tag.previous_sibling
        next_sibling = tag.next_sibling
        prev_sibling_text = prev_sibling.strip() if prev_sibling and isinstance(prev_sibling, str) and prev_sibling.strip() else None
        next_sibling_text = next_sibling.strip() if next_sibling and isinstance(next_sibling, str) and next_sibling.strip() else None

        # New Generic Check
        if aria_label or role == 'img' or has_icon_or_logo_in_class or (is_empty_or_nested_only and tag_classes):
            elements["icons"].append({
                "tag": tag.name, 
                "classes": tag_classes, 
                "aria_label": aria_label, 
                "text": icon_text, 
                "role": role, 
                "parent": parent_info,
                "prev_sibling_text": prev_sibling_text,
                "next_sibling_text": next_sibling_text,
                "sequential_index": icon_index
                })
            icon_index += 1 
            element_count += 1
            if element_count >= max_elements: break 
            continue 
             
    # Attempt 2: Find <svg> elements
    for svg in soup.find_all("svg"):
        if element_count >= max_elements: break # Early exit
        aria_label = svg.get("aria-label")
        role = svg.get("role")
        title_tag = svg.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else None
        identifier = aria_label or title_text 
        
        # Context capture - Adding parent ID
        parent_info = None
        if svg.parent:
             parent_info = {
                "tag": svg.parent.name, 
                "classes": svg.parent.get('class', []),
                "id": svg.parent.get('id') # Capture parent ID
            }
        prev_sibling = svg.previous_sibling
        next_sibling = svg.next_sibling
        prev_sibling_text = prev_sibling.strip() if prev_sibling and isinstance(prev_sibling, str) and prev_sibling.strip() else None
        next_sibling_text = next_sibling.strip() if next_sibling and isinstance(next_sibling, str) and next_sibling.strip() else None
        
        if role == "img" or identifier:
             if not any(p.name in ['a', 'button'] for p in svg.parents):
                elements["icons"].append({
                    "tag": svg.name, 
                    "role": role, 
                    "aria_label": aria_label, 
                    "title": title_text,    
                    "identifier_used": identifier, 
                    "parent": parent_info, # Now includes ID if present
                    "prev_sibling_text": prev_sibling_text,
                    "next_sibling_text": next_sibling_text,
                    "sequential_index": icon_index 
                    })
                icon_index += 1 
                element_count += 1
                if element_count >= max_elements: break # Check after increment
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v} # Check after loop

    # Forms (form) - *** REVISED LOGIC ***
    form_index = 0 # Index for forms
    for form in soup.find_all("form"):
        if element_count >= max_elements: break
        # --- Determine Form Identifier ---
        form_id = form.get("id")
        form_aria_label = form.get("aria-label")
        form_identifier = None
        
        if form_aria_label:
            form_identifier = f"the form labelled '{form_aria_label}'"
        elif form_id:
            form_identifier = f"the form with ID '{form_id}'"
        else:
            # *** REVISED IDENTIFIER LOGIC ***
            identifier_found = False
            
            # 3. Check custom data attribute
            data_di_id = form.get("data-di-form-id")
            if data_di_id:
                form_identifier = f"the '{data_di_id}' form"
                identifier_found = True
                
            # 4. Check for legend
            if not identifier_found:
                legend = form.find("legend")
                if legend and legend.get_text(strip=True):
                     form_identifier = f"the '{legend.get_text(strip=True)}' form"
                     identifier_found = True

            # 5. Check for heading INSIDE the form
            if not identifier_found:
                internal_heading = form.find([f'h{i}' for i in range(1, 7)])
                if internal_heading and internal_heading.get_text(strip=True):
                    form_identifier = f"the '{internal_heading.get_text(strip=True)}' form"
                    identifier_found = True

            # 6. Check immediate preceding sibling heading
            if not identifier_found:
                prev_sibling = form.find_previous_sibling()
                if prev_sibling and prev_sibling.name in [f'h{i}' for i in range(1, 7)]:
                    heading_text = prev_sibling.get_text(strip=True)
                    if heading_text:
                        form_identifier = f"the form under the '{heading_text}' heading"
                        identifier_found = True
            
            # 7. Check PARENT's previous sibling heading
            if not identifier_found and form.parent:
                parent_prev_sibling = form.parent.find_previous_sibling()
                if parent_prev_sibling and parent_prev_sibling.name in [f'h{i}' for i in range(1, 7)]:
                    heading_text = parent_prev_sibling.get_text(strip=True)
                    if heading_text:
                        parent_tag = form.parent.name
                        form_identifier = f"the form within the parent {parent_tag} under the '{heading_text}' heading"
                        identifier_found = True
            
            # 8. Check if it's a login form
            if not identifier_found:
                # Look for login-related cues
                login_indicators = ['login', 'log in', 'signin', 'sign in', 'logon', 'log on']
                
                # Check for login-related classes on form
                form_classes = form.get('class', [])
                if any(cls and any(indicator in cls.lower() for indicator in login_indicators) for cls in form_classes):
                    form_identifier = "the login form"
                    identifier_found = True
                
                # Check for login-related ids on form
                if form_id and any(indicator in form_id.lower() for indicator in login_indicators):
                    form_identifier = "the login form"
                    identifier_found = True
                    
                # Check if there are username/email and password fields
                username_field = form.find(['input'], attrs={'name': lambda x: x and any(name in x.lower() for name in ['user', 'email', 'username', 'login'])})
                password_field = form.find(['input'], attrs={'type': 'password'})
                
                if username_field and password_field:
                    form_identifier = "the login form"
                    identifier_found = True
                
            # 9. Fallback to index ONLY if all other methods fail
            if not identifier_found:
                form_identifier = f"form #{form_index + 1}"

        # --- Initialize form details ---
        form_details = {
            "form_identifier": form_identifier,
            "tag": form.name, 
            "id": form_id, 
            "action": form.get("action", ""), 
            "method": form.get("method", "get").lower(), 
            "inputs": [], 
            "submit_button": None 
        }
        
        # --- Find inputs and submit button within the form ---
        form_elements = form.find_all(["input", "textarea", "select", "button"])
        
        for inp in form_elements:
            # Skip hidden inputs
            if inp.name == "input" and inp.get("type") == "hidden": 
                continue

            # --- Check if it's a submit button ---
            is_submit = (inp.name == "button" and inp.get("type", "submit").lower() == "submit") or \
                        (inp.name == "input" and inp.get("type", "").lower() == "submit")

            if is_submit:
                # Only capture the first submit button found for now
                if form_details["submit_button"] is None:
                    submit_text = ""
                    if inp.name == "input":
                        submit_text = inp.get("value", "").strip()
                    if not submit_text: # Fallback for <button> or if input value is empty
                        submit_text = inp.get_text(strip=True)
                    if not submit_text: # Fallback if text is empty
                         submit_text = "Submit" # Default text

                    # Create a simple identifier for the prompt
                    submit_identifier = f"the '{submit_text}' button"
                    # Add more detail if needed (e.g., ID)
                    submit_id = inp.get("id")
                    if submit_id:
                        submit_identifier += f" with ID '{submit_id}'"
                        
                    form_details["submit_button"] = {
                        "text": submit_text,
                        "identifier": submit_identifier,
                        "tag": inp.name,
                        "id": submit_id
                    }
                continue # Move to next element once submit button is found/processed

            # --- Process regular input fields (input, select, textarea) ---
            inp_tag = inp.name
            inp_type = inp.get("type", inp_tag) # Use tag name as type for select/textarea
            inp_id = inp.get("id")
            inp_name = inp.get("name")
            inp_placeholder = inp.get("placeholder")
            inp_aria_label = inp.get("aria-label")
            inp_required = inp.has_attr('required')
            
            # Find associated label
            label_text = ""
            if inp_id:
                label_tag = form.find("label", {"for": inp_id})
                if label_tag: 
                    label_text = label_tag.get_text(strip=True)
            # If no label, try parent label if input is inside one
            if not label_text and inp.parent and inp.parent.name == "label":
                 label_text = inp.parent.get_text(strip=True)

            # Determine the best identifier string for the prompt
            field_identifier = ""
            if label_text:
                field_identifier = f"'{label_text}' field"
            elif inp_placeholder:
                field_identifier = f"field with placeholder '{inp_placeholder}'"
            elif inp_aria_label:
                 field_identifier = f"field labelled '{inp_aria_label}'"
            elif inp_name:
                field_identifier = f"field named '{inp_name}'"
            elif inp_id:
                 field_identifier = f"field with ID '{inp_id}'"
            else:
                field_identifier = f"{inp_type} field" # Fallback

            form_details["inputs"].append({
                "identifier": field_identifier,
                "tag": inp_tag, 
                "type": inp_type, 
                "name": inp_name, 
                "id": inp_id,
                "required": inp_required
            })

        # --- Add form to results if it has inputs and a submit button ---
        if form_details["inputs"] and form_details["submit_button"]:
            elements["forms"].append(form_details)
            form_index += 1
            element_count += 1 # Count this form as one element

    if element_count >= max_elements: return {k: v for k, v in elements.items() if v}
    
    # Semantic Structure Elements
    for tag_name in semantic_tags:
        if element_count >= max_elements: break
        found_tags = soup.find_all(tag_name)
        if found_tags:
            elements["semantic_elements"].append({"tag": tag_name, "count": len(found_tags)})
            element_count += 1 # Count each type of semantic tag found as one element for simplicity
    # Note: element_count check here is approximate as we count tag *types*
    if element_count >= max_elements: return {k: v for k, v in elements.items() if v} 
        
    # --- Final Cleanup --- 
    # Remove empty categories before returning
    elements = {k: v for k, v in elements.items() if v}
        
    return elements

def add_uniqueness_context(elements_data: List[Dict[str, Any]], primary_key: str, context_hierarchy: List[str]) -> List[Dict[str, Any]]:
    """
    Analyzes a list of extracted elements to determine and add the minimum context 
    needed to uniquely identify elements that share the same primary identifier.
    Uses an iterative refinement approach based on the context hierarchy.

    Args:
        elements_data: List of element dictionaries.
        primary_key: Key for the primary identifier (e.g., 'text_snippet').
        context_hierarchy: Ordered list of context keys (e.g., ['id', 'parent.id', ...]).

    Returns:
        The list of element dictionaries, augmented with 'uniqueness_context' where needed.
    """
    from collections import defaultdict
    import copy # To avoid modifying dicts while iterating

    # --- Helper to get nested values (slightly modified for clarity) ---
    def get_nested_value(data_dict, key_path):
        keys = key_path.split('.')
        current_value = data_dict
        try:
            # Handle special composite keys first
            if key_path == 'sibling_text':
                # Prefer next sibling text, fallback to previous
                return data_dict.get('next_sibling_text') or data_dict.get('prev_sibling_text')
            elif key_path == 'parent_classes':
                parent_info = data_dict.get('parent')
                if parent_info:
                    p_classes = parent_info.get('classes')
                    return " ".join(p_classes) if p_classes else None
                return None
            elif key_path == 'parent_description':
                parent_info = data_dict.get('parent')
                if parent_info:
                    desc = parent_info.get('tag', 'element')
                    parent_id = parent_info.get('id')
                    parent_classes = parent_info.get('classes')
                    if parent_id:
                        return f"{desc} with ID \"{parent_id}\""
                    elif parent_classes:
                        return f"{desc} with classes \"{' '.join(parent_classes)}\""
                    else:
                        return f"parent {desc}"
                return None
            elif key_path == 'href':
                # For links, use the last part of the URL as context
                href = data_dict.get('href', '')
                if href:
                    # Remove protocol and domain
                    href = href.split('//')[-1].split('/', 1)[-1]
                    # Remove trailing slash and query parameters
                    href = href.rstrip('/').split('?')[0]
                    return href
                return None

            # Handle standard keys (nested or direct)
            for key in keys:
                if isinstance(current_value, dict):
                    current_value = current_value.get(key)
                else:
                    return None # Cannot traverse further
                if current_value is None:
                    return None

            # Handle list values like 'classes' directly on the element
            if key_path == 'classes' and isinstance(current_value, list):
                return " ".join(current_value) if current_value else None
                
            # Return the final value if it's not a list (or if it's a list but not 'classes')
            return current_value if not isinstance(current_value, list) else current_value 

        except (AttributeError, TypeError):
            return None
    # --- End Helper --- 

    # Add original index to track elements easily
    for i, element in enumerate(elements_data):
        element['_original_index'] = i

    # Initial grouping based on primary key
    initial_groups = defaultdict(list)
    for element in elements_data:
        primary_value = get_nested_value(element, primary_key)
        # Group even if primary value is None/empty, to handle those cases
        initial_groups[primary_value].append(element)

    processed_elements_data = [None] * len(elements_data) # Prepare result list

    # Process each initial group
    for primary_value, group in initial_groups.items():
        if len(group) == 1:
            # Unique group, no context needed (just copy to result)
            element = group[0]
            original_idx = element.pop('_original_index') # Remove tracker before storing
            processed_elements_data[original_idx] = element
            continue

        # Ambiguous group, needs context
        ambiguous_subgroup = copy.deepcopy(group) # Work on a copy
        resolved_in_this_group = {} # Track resolved elements: original_index -> context_level

        for context_level_key in context_hierarchy:
            if not ambiguous_subgroup: # Stop if all resolved
                break

            # Subdivide the current ambiguous subgroup by the current context level
            subgroups_at_this_level = defaultdict(list)
            elements_still_ambiguous_next = []

            for element in ambiguous_subgroup:
                context_value = get_nested_value(element, context_level_key)
                # Treat None context value as a distinct group
                subgroups_at_this_level[context_value].append(element)
            
            # Check the new subgroups
            for context_value, subgroup in subgroups_at_this_level.items():
                if len(subgroup) == 1:
                    # Element resolved at this level!
                    resolved_element = subgroup[0]
                    original_idx = resolved_element['_original_index']
                    # Only add context if not already resolved at an earlier level
                    if original_idx not in resolved_in_this_group:
                         if context_value is not None: # Don't add context if resolved by lacking a value others had
                             # For links, prefer href over ID when possible
                             if context_level_key == 'id' and primary_key == 'text':
                                 href = get_nested_value(resolved_element, 'href')
                                 if href:
                                     resolved_element['uniqueness_context'] = {
                                         'level': 'href',
                                         'value': href
                                     }
                                 else:
                                     resolved_element['uniqueness_context'] = {
                                         'level': context_level_key,
                                         'value': context_value
                                     }
                             else:
                                 resolved_element['uniqueness_context'] = {
                                     'level': context_level_key,
                                     'value': context_value
                                 }
                         resolved_in_this_group[original_idx] = context_level_key # Mark as resolved
                         # Remove tracker and place in result list
                         resolved_element.pop('_original_index') 
                         processed_elements_data[original_idx] = resolved_element
                else:
                    # Subgroup still ambiguous, carry over to next context level check
                    elements_still_ambiguous_next.extend(subgroup)

            # Update the list of elements still needing resolution
            ambiguous_subgroup = elements_still_ambiguous_next

        # After checking all context levels, any remaining elements are truly ambiguous
        for ambiguous_element in ambiguous_subgroup:
             original_idx = ambiguous_element.pop('_original_index')
             # Add to results without uniqueness_context
             processed_elements_data[original_idx] = ambiguous_element 

    # Clean up any potential None entries if something went wrong (shouldn't happen)
    final_data = [elem for elem in processed_elements_data if elem is not None]
    return final_data

def determine_link_type(dom_context: Dict) -> str:
    """Determine the type of link based on its DOM context."""
    # Check for menu items with more specific conditions
    if any(parent.get('role') == 'menuitem' for parent in dom_context["interactive_parents"]):
        # Check if it's a submenu item
        if any(parent.get('aria-expanded') is not None for parent in dom_context["interactive_parents"]):
            return "submenu_item"
        return "menu_item"
    
    # Check for dropdown items with more specific conditions
    if any(parent.get('aria-controls') is not None for parent in dom_context["interactive_parents"]):
        # Check if it's a dropdown trigger
        if any(parent.get('aria-expanded') is not None for parent in dom_context["interactive_parents"]):
            return "dropdown_trigger"
        return "dropdown_item"
    
    # Check for accordion items
    if any(parent.get('aria-expanded') is not None for parent in dom_context["interactive_parents"]):
        return "accordion_item"
    
    # Check for tab items
    if any(parent.get('role') == 'tab' for parent in dom_context["interactive_parents"]):
        return "tab_item"
    
    # Check for navigation items with more specific conditions
    if any(parent.get('role') == 'navigation' for parent in dom_context["ancestors"]):
        # Check if it's in a specific navigation section
        if any('header' in parent.get('class', []) for parent in dom_context["ancestors"]):
            return "header_nav_item"
        if any('footer' in parent.get('class', []) for parent in dom_context["ancestors"]):
            return "footer_nav_item"
        if any('sidebar' in parent.get('class', []) for parent in dom_context["ancestors"]):
            return "sidebar_nav_item"
        return "nav_item"
    
    # Check for breadcrumb items
    if any(parent.get('role') == 'navigation' and 'breadcrumb' in parent.get('aria-label', '').lower() for parent in dom_context["ancestors"]):
        return "breadcrumb_item"
    
    # Check for pagination items
    if any(parent.get('role') == 'navigation' and 'pagination' in parent.get('aria-label', '').lower() for parent in dom_context["ancestors"]):
        return "pagination_item"
    
    # Check for footer links
    if any(parent.name == 'footer' for parent in dom_context["ancestors"]):
        return "footer_link"
    
    # Check for header links
    if any(parent.name == 'header' for parent in dom_context["ancestors"]):
        return "header_link"
    
    # Check for sidebar links
    if any('sidebar' in parent.get('class', []) for parent in dom_context["ancestors"]):
        return "sidebar_link"
    
    # Check for social media links
    if any('social' in parent.get('class', []) for parent in dom_context["ancestors"]):
        return "social_link"
    
    # Check for action links (e.g., "Read More", "Learn More", etc.)
    action_texts = ['read more', 'learn more', 'view', 'see', 'click here', 'get started']
    if any(text.lower() in dom_context["element"].get('text', '').lower() for text in action_texts):
        return "action_link"
    
    # Default to regular link
    return "regular_link"
