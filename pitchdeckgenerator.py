import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
from fpdf import FPDF
import requests
from PIL import Image
from io import BytesIO
import json
import time

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)

def generate_pitch_content(idea):
    model = genai.GenerativeModel('gemini-pro')
    
    pitch_prompt = f"""Create a comprehensive pitch deck content for: {idea}
    Include the following sections:
    1. Problem Statement
    2. Solution Overview
    3. Market Opportunity
    4. Business Model
    5. Competition Analysis
    6. Go-to-Market Strategy
    7. Financial Projections
    8. Team
    9. Investment Ask
    
    For each section:
    - Provide clear, concise content
    - Include key metrics and data points
    - Focus on compelling narrative
    - Keep it investor-friendly
    
    IMPORTANT: Your response must be a valid JSON object with section names as keys and content as values.
    Do not include any text outside the JSON structure.
    Example format: {{
        "Problem Statement": "content here",
        "Solution Overview": "content here"
    }}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(pitch_prompt)
            # Try to parse the response as JSON
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                # Look for content between curly braces
                text = response.text
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = text[start_idx:end_idx + 1]
                    return json.loads(json_str)
                raise ValueError("Could not extract valid JSON from response")
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise Exception(f"Failed to generate pitch content after {max_retries} attempts: {str(e)}")
            time.sleep(1)  # Wait before retrying

def create_slide_image(content, section):
    # Vercel OG API endpoint
    og_api_url = "https://og-image.vercel.app"
    
    # Create a clean, minimalistic design with the content
    text = f"{section}\n\n{content[:200]}..." # Truncate content for better fit
    
    # Define custom styles based on section type
    styles = {
        "Problem Statement": "bg-gradient-to-r from-red-500 to-orange-500 text-white p-20",
        "Solution Overview": "bg-gradient-to-r from-blue-500 to-cyan-500 text-white p-20",
        "Market Opportunity": "bg-gradient-to-r from-green-500 to-teal-500 text-white p-20",
        "Business Model": "bg-gradient-to-r from-purple-500 to-pink-500 text-white p-20",
        "Competition Analysis": "bg-gradient-to-r from-yellow-500 to-orange-500 text-white p-20",
        "Go-to-Market Strategy": "bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-20",
        "Financial Projections": "bg-gradient-to-r from-emerald-500 to-green-500 text-white p-20",
        "Team": "bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-20",
        "Investment Ask": "bg-gradient-to-r from-violet-500 to-purple-500 text-white p-20"
    }
    
    # Get style for current section or use default
    style = styles.get(section, "bg-gradient-to-r from-gray-700 to-gray-900 text-white p-20")
    
    # Add common styles for modern look
    style += " font-sans rounded-xl shadow-2xl mx-auto max-w-4xl"
    
    # Create HTML content with custom styling
    html_content = f"<div class=\"{style}\"><h1 class=\"text-4xl font-bold mb-8\">{section}</h1><p class=\"text-xl leading-relaxed\">{content[:200]}...</p></div>"
    
    # Encode the HTML content for URL
    encoded_text = requests.utils.quote(html_content)
    
    # Generate OG image URL with custom parameters and no Vercel logo
    image_url = f"{og_api_url}/{encoded_text}.png?theme=light&md=1&fontSize=75px"
    
    # Download the generated image
    response = requests.get(image_url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        raise Exception(f"Failed to generate image for section {section}")

def generate_pdf(idea, content, images):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add title slide
    pdf.add_page()
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(0, 40, idea, ln=True, align='C')
    pdf.set_font('Arial', 'I', 16)
    pdf.cell(0, 10, 'AI Generated Pitch Deck', ln=True, align='C')
    
    # Add content slides with images
    for section, text in content.items():
        pdf.add_page()
        
        # Add the Vercel OG generated image
        if section in images:
            img = images[section]
            # Convert PIL Image to bytes
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Save temporary image file
            temp_img_path = f'temp_{section}.png'
            with open(temp_img_path, 'wb') as f:
                f.write(img_byte_arr)
            
            # Add image to PDF
            pdf.image(temp_img_path, x=10, y=10, w=277)
            
            # Clean up temporary file
            os.remove(temp_img_path)
        
        # Add section content
        pdf.set_y(140)  # Position text below image
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 10, section, ln=True, align='L')
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 10, text)
    
    # Save PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{idea.lower().replace(' ', '_')}_pitch_{timestamp}.pdf"
    pdf.output(filename)
    return filename

def main():
    print("Welcome to the AI Pitch Deck Generator!")
    idea = input("Enter your product/business idea: ")
    
    print("\nGenerating pitch deck content...")
    content = generate_pitch_content(idea)
    
    print("\nCreating slide designs...")
    images = {section: create_slide_image(text, section) 
             for section, text in content.items()}
    
    print("\nCompiling PDF...")
    filename = generate_pdf(idea, content, images)
    
    print(f"\nPitch deck has been saved to {filename}")

if __name__ == "__main__":
    main()