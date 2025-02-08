import google.generativeai as genai
import os
from datetime import datetime
import requests
import base64
from dotenv import load_dotenv
import time

load_dotenv()

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

genai.configure(api_key="AIzaSyDBkLQdslFWHzqF7CYQlT9YLjedrX4DdQA")

def generate_outline(model, topic):
    outline_prompt = f"""Create a detailed outline for a long-form Medium blog post about {topic}.
    The outline should include:
    1. An engaging headline
    2. 5-7 main sections
    3. Key points for each section
    4. Potential data points or research areas
    5. Personal story angles
    Format as a structured Markdown outline."""
    
    outline_response = model.generate_content(outline_prompt)
    return outline_response.text

def generate_section(model, topic, section_title, context):
    section_prompt = f"""Write a detailed section for a Medium blog post about {topic}.
    Section title: {section_title}
    Context: {context}
    
    Requirements:
    1. Write 400-600 words
    2. Include specific examples and details
    3. Incorporate relevant statistics or research points
    4. Use engaging storytelling techniques
    5. Maintain a conversational yet professional tone
    6. Ensure smooth transitions
    Format in Markdown."""
    
    section_response = model.generate_content(section_prompt)
    return section_response.text

def refine_content(model, content, focus):
    refine_prompt = f"""Improve this blog post section with a focus on {focus}:
    
    {content}
    
    Requirements:
    1. Enhance clarity and flow
    2. Add more specific examples
    3. Strengthen emotional resonance
    4. Improve transitions
    5. Maintain Medium's style and tone
    Return the refined content in Markdown."""
    
    refine_response = model.generate_content(refine_prompt)
    return refine_response.text

def generate_story(topic):
    # Initialize Gemini Pro model
    model = genai.GenerativeModel('gemini-pro')
    
    print("\nGenerating outline...")
    outline = generate_outline(model, topic)
    
    print("\nGenerating sections...")
    sections = []
    current_context = outline
    
    # Extract section titles from outline (simplified example)
    section_titles = [line.strip('# ').strip() 
                     for line in outline.split('\n') 
                     if line.strip().startswith('##')]
    
    for section_title in section_titles:
        print(f"\nWriting section: {section_title}")
        section_content = generate_section(model, topic, section_title, current_context)
        sections.append(section_content)
        
        # Allow API rate limiting
        time.sleep(2)
        
        # Refine the section
        print(f"Refining section: {section_title}")
        refined_content = refine_content(model, section_content, "engagement and depth")
        sections[-1] = refined_content
        
        # Update context with the latest content
        current_context = '\n\n'.join(sections)
        
        time.sleep(2)
    
    # Generate image suggestions
    image_prompt = f"""Suggest 3 professional image descriptions that would enhance this blog post about {topic}.
    Each image should:
    1. Illustrate key concepts
    2. Be visually striking
    3. Fit Medium's aesthetic
    4. Support the narrative
    Make them detailed and specific."""
    
    image_descriptions = model.generate_content(image_prompt).text.split('\n')
    
    # For now, use placeholder images
    image_urls = [
        "https://via.placeholder.com/1200x600",
        "https://via.placeholder.com/1200x600",
        "https://via.placeholder.com/1200x600"
    ]
    
    # Combine all content
    full_content = outline + '\n\n'
    for i, section in enumerate(sections):
        if i < len(image_urls):
            full_content += f"\n![Blog Image]({image_urls[i]})\n\n"
        full_content += section + '\n\n'
    
    # Add image descriptions as comments
    full_content += "\n\n<!-- Image Descriptions:\n"
    for desc in image_descriptions:
        if desc.strip():
            full_content += f"- {desc.strip()}\n"
    full_content += "-->"
    
    return full_content

def save_story(content, product_idea):
    # Create a clean filename
    clean_name = product_idea.lower().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{clean_name}_marketing_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(content)
    
    return filename

def main():
    print("Welcome to the AI Marketing Story Generator!")
    product_idea = input("Enter your product idea: ")
    
    print("\nGenerating your marketing story...")
    story_content = generate_story(product_idea)
    
    filename = save_story(story_content, product_idea)
    print(f"\nMarketing story has been saved to {filename}")

if __name__ == "__main__":
    main()