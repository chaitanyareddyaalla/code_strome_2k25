import json
from datetime import datetime
from dotenv import load_dotenv
import os
import sys
import re
import google.generativeai as genai
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# Load environment variables and configure
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOG_FILE = os.getenv("LOG_FILE_NAME") or "health_log.json"

# Configure AI Model
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    USE_AI = True
else:
    print(f"{Fore.RED}⚠️  Error: GEMINI_API_KEY not found. AI features will not work.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Please set the GEMINI_API_KEY environment variable and restart.{Style.RESET_ALL}")
    USE_AI = False
    if input("Continue with limited functionality? (y/n): ").lower() != 'y':
        sys.exit(1)

def load_health_history():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def display_menu():
    print(f"\n{Fore.CYAN}{Back.BLACK}" + "═" * 60 + f"{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Back.BLACK}✨ Welcome to Your {Fore.YELLOW}Personal Health & Well-being Bot{Fore.CYAN} ✨{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Back.BLACK}" + "═" * 60 + f"{Style.RESET_ALL}")
    print(f"{Fore.WHITE}What would you like to do today?\n")
    print(f"{Fore.GREEN}1️⃣  {Fore.WHITE}Chat about how you're feeling")
    print(f"{Fore.GREEN}2️⃣  {Fore.WHITE}View previous health logs")
    print(f"{Fore.GREEN}3️⃣  {Fore.WHITE}Learn about seasonal illnesses & precautions")
    print(f"{Fore.GREEN}4️⃣  {Fore.WHITE}Exit")
    print(f"{Fore.CYAN}" + "─" * 60 + f"{Style.RESET_ALL}")
    choice = input(f"{Fore.YELLOW}Enter your choice (1-4): {Style.RESET_ALL}")
    return choice.strip()

# Get AI Suggestions with context and structured output
def get_ai_suggestions(symptoms, mood, additional_info=None):
    health_history = load_health_history()
    
    context = ""
    if health_history:
        context = "Previous health issues:\n"
        for entry in health_history[-3:]:
            context += f"- Date: {entry['timestamp']}, Symptoms: {entry['physical_symptoms']}, "
            context += f"Mood: {entry['mood_rating']}, Issues: {entry.get('possible_issues', 'None')}\n"
    
    prompt = f"""The user is a student living in a hostel reporting symptoms: '{symptoms}'.
    Mood rating: {mood}/5.
    Additional info: {additional_info or 'None provided'}
    
    {context}
    
    Please analyze this information and provide a health assessment with the following structure:
    
    [POSSIBLE_ISSUES]
    List 2-3 possible health issues with likelihood percentages (e.g., Common Cold: 70%)
    [/POSSIBLE_ISSUES]
    
    [SELF_CARE_TIPS]
    Provide 2-3 specific self-care tips for a hostel environment
    [/SELF_CARE_TIPS]
    
    [HOSTEL_SPECIFIC]
    Add 1-2 specific recommendations for managing in a hostel setting
    [/HOSTEL_SPECIFIC]
    
    [CONTAGION_ALERT]
    Mention if these symptoms could indicate something contagious in a hostel setting
    [/CONTAGION_ALERT]
    
    [FOOD_QUESTION]
    If food-related symptoms are mentioned, include a question about whether others have similar issues
    [/FOOD_QUESTION]
    
    [MEDICAL_ADVICE]
    Advise if medical attention is needed, especially for serious or persistent symptoms
    [/MEDICAL_ADVICE]
    
    Keep advice practical for hostel students with limited resources."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"{Fore.RED}⚠️  Error communicating with Gemini: {e}{Style.RESET_ALL}")
        return "Sorry, AI suggestions are unavailable at the moment."

def parse_ai_response(ai_text):
    # Extract sections using regex
    sections = {
        'possible_issues': re.search(r'\[POSSIBLE_ISSUES\](.*?)\[/POSSIBLE_ISSUES\]', ai_text, re.DOTALL),
        'self_care_tips': re.search(r'\[SELF_CARE_TIPS\](.*?)\[/SELF_CARE_TIPS\]', ai_text, re.DOTALL),
        'hostel_specific': re.search(r'\[HOSTEL_SPECIFIC\](.*?)\[/HOSTEL_SPECIFIC\]', ai_text, re.DOTALL),
        'contagion_alert': re.search(r'\[CONTAGION_ALERT\](.*?)\[/CONTAGION_ALERT\]', ai_text, re.DOTALL),
        'food_question': re.search(r'\[FOOD_QUESTION\](.*?)\[/FOOD_QUESTION\]', ai_text, re.DOTALL),
        'medical_advice': re.search(r'\[MEDICAL_ADVICE\](.*?)\[/MEDICAL_ADVICE\]', ai_text, re.DOTALL)
    }
    
    result = {}
    for key, match in sections.items():
        if match:
            content = match.group(1).strip()
            result[key] = content
        else:
            result[key] = ""
    
    # Format for display and logging
    possible_issues = result.get('possible_issues', "No specific issues identified.")
    
    remedy_advice = []
    if result.get('self_care_tips'):
        remedy_advice.append("Self-Care Tips:")
        remedy_advice.append(result['self_care_tips'])
    
    if result.get('hostel_specific'):
        remedy_advice.append("\nHostel-Specific Tips:")
        remedy_advice.append(result['hostel_specific'])
    
    if result.get('contagion_alert'):
        remedy_advice.append("\nContagion Alert:")
        remedy_advice.append(result['contagion_alert'])
    
    if result.get('medical_advice'):
        remedy_advice.append("\nMedical Advice:")
        remedy_advice.append(result['medical_advice'])
    
    return {
        'possible_issues': possible_issues,
        'remedy_advice': "\n".join(remedy_advice),
        'food_question': result.get('food_question', ""),
        'raw_ai_response': ai_text
    }

def handle_chat():
    print(f"\n{Fore.BLUE}🗣️  Let's talk about your health.{Style.RESET_ALL}")
    physical_symptoms = input(f"{Fore.WHITE}Describe any physical symptoms (e.g., fever, headache): {Style.RESET_ALL}").strip().lower()

    additional_info = ""
    
    # Ask relevant follow-up questions based on symptoms
    if any(term in physical_symptoms for term in ["stomach", "vomit", "nausea", "food", "eating", "diarrhea"]):
        others_affected = input(f"{Fore.YELLOW}Are others in your hostel experiencing similar symptoms? (yes/no): {Style.RESET_ALL}").strip().lower()
        additional_info += f"Others affected: {others_affected}. "
    
    if "fever" in physical_symptoms:
        temperature = input(f"{Fore.YELLOW}If you've measured your temperature, what is it? (or 'not measured'): {Style.RESET_ALL}").strip()
        additional_info += f"Temperature: {temperature}. "
    
    duration = input(f"{Fore.YELLOW}How long have you been experiencing these symptoms? (e.g., 2 days): {Style.RESET_ALL}").strip()
    additional_info += f"Duration: {duration}. "

    while True:
        mood_str = input(f"{Fore.YELLOW}Rate your mood (1 = very low, 5 = excellent): {Style.RESET_ALL}").strip()
        if mood_str.isdigit() and 1 <= int(mood_str) <= 5:
            mood_rating = int(mood_str)
            break
        else:
            print(f"{Fore.RED}⚠️  Please enter a number between 1 and 5.{Style.RESET_ALL}")

    print(f"\n{Fore.MAGENTA}🤔 Processing your input with AI...{Style.RESET_ALL}\n")

    if USE_AI:
        raw_ai_response = get_ai_suggestions(physical_symptoms, mood_rating, additional_info)
        parsed_response = parse_ai_response(raw_ai_response)
        
        if parsed_response['food_question'] and "others affected" not in additional_info.lower():
            print(f"{Fore.YELLOW}{parsed_response['food_question']}{Style.RESET_ALL}")
            food_response = input(f"{Fore.WHITE}Your answer: {Style.RESET_ALL}").strip()
            additional_info += f" Food question response: {food_response}."
        
        # Display formatted results
        print(f"{Fore.GREEN}🤖 AI Health Assessment:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}" + "─" * 60 + f"{Style.RESET_ALL}")
        
        # Highlight issues based on severity percentage
        issues = parsed_response['possible_issues']
        issues_with_percentages = re.findall(r'(.*?)(\d+%)', issues)
        
        print(f"{Fore.YELLOW}🩺 Possible Issues:{Style.RESET_ALL}")
        if issues_with_percentages:
            for issue, percentage in issues_with_percentages:
                percentage_int = int(percentage.strip('%'))
                if percentage_int >= 70:
                    percentage_color = Fore.RED
                elif percentage_int >= 50:
                    percentage_color = Fore.YELLOW
                else:
                    percentage_color = Fore.GREEN
                
                print(f"{Fore.WHITE}  • {issue.strip()}{percentage_color}{percentage}{Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE}  {issues}{Style.RESET_ALL}")
        
        # Remedies and advice with colored sections
        print(f"\n{Fore.YELLOW}💊 Recommendations:{Style.RESET_ALL}")
        advice = parsed_response['remedy_advice']
        advice = advice.replace("Self-Care Tips:", f"{Fore.GREEN}Self-Care Tips:{Style.RESET_ALL}")
        advice = advice.replace("Hostel-Specific Tips:", f"{Fore.GREEN}Hostel-Specific Tips:{Style.RESET_ALL}")
        advice = advice.replace("Contagion Alert:", f"{Fore.RED}Contagion Alert:{Style.RESET_ALL}")
        advice = advice.replace("Medical Advice:", f"{Fore.RED}Medical Advice:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{advice}{Style.RESET_ALL}")
        
        suggestions_to_log = {
            "possible_issues": parsed_response['possible_issues'],
            "remedy_advice": parsed_response['remedy_advice'],
            "raw_ai_response": parsed_response['raw_ai_response']
        }
    else:
        print(f"{Fore.RED}AI analysis not available. Please set up your GEMINI_API_KEY.{Style.RESET_ALL}")
        suggestions_to_log = {
            "possible_issues": "AI not available",
            "remedy_advice": "Please set up API key for health analysis."
        }

    save_log = input(f"\n{Fore.BLUE}💾 Save this health log? (yes/no): {Style.RESET_ALL}").strip().lower()
    if save_log == 'yes':
        save_to_log(physical_symptoms, mood_rating, suggestions_to_log, additional_info)
        print(f"{Fore.GREEN}✅ Log saved successfully!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Log not saved.{Style.RESET_ALL}")

def save_to_log(symptoms, mood, suggestions, additional_info=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "physical_symptoms": symptoms,
        "mood_rating": mood,
        "additional_info": additional_info or "",
        "possible_issues": suggestions['possible_issues'],
        "remedy_advice": suggestions['remedy_advice']
    }
    
    if 'raw_ai_response' in suggestions:
        log_entry["raw_ai_response"] = suggestions['raw_ai_response']
    
    try:
        with open(LOG_FILE, 'r+') as f:
            data = json.load(f)
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(LOG_FILE, 'w') as f:
            json.dump([log_entry], f, indent=4)

def view_logs():
    print(f"\n{Fore.BLUE}📜 --- Previous Health Logs --- 📜{Style.RESET_ALL}")
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
            if not data:
                print(f"\n{Fore.YELLOW}📂 No logs found yet.{Style.RESET_ALL}")
            else:
                show_raw = input(f"{Fore.YELLOW}Show raw AI responses? (yes/no): {Style.RESET_ALL}").strip().lower() == 'yes'
                
                for i, entry in enumerate(data):
                    print(f"\n{Fore.CYAN}" + "─" * 60 + f"{Style.RESET_ALL}")
                    print(f"{Fore.BLUE}🗓️  {entry['timestamp']} {Fore.YELLOW}(Log #{i+1}){Style.RESET_ALL}")
                    print(f"{Fore.RED}🤕 Symptoms: {Fore.WHITE}{entry['physical_symptoms']}{Style.RESET_ALL}")
                    if 'additional_info' in entry and entry['additional_info']:
                        print(f"{Fore.YELLOW}ℹ️  Additional Info: {Fore.WHITE}{entry['additional_info']}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}😊 Mood Rating: {Fore.WHITE}{entry['mood_rating']}{Style.RESET_ALL}")
                    print(f"{Fore.MAGENTA}🩺 Possible Issues: {Fore.WHITE}{entry['possible_issues']}{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}💊 Remedies/Advice:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{entry['remedy_advice']}{Style.RESET_ALL}")
                    
                    if show_raw and 'raw_ai_response' in entry:
                        print(f"\n{Fore.YELLOW}🤖 Raw AI Response:{Style.RESET_ALL}")
                        print(f"{Fore.WHITE}{entry['raw_ai_response']}{Style.RESET_ALL}")
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"\n{Fore.RED}⚠️  No logs available.{Style.RESET_ALL}")

# Get AI-powered seasonal health info based on current date
def get_ai_seasonal_info():
    current_month = datetime.now().strftime('%B')
    location = "Hyderabad"  # Default location
    
    prompt = f"""Create a health advisory for hostel students in {location} during the month of {current_month}.
    Include:
    1. Top 5 common seasonal illnesses for this location and month
    2. For each illness:
       - Symptoms to watch for
       - Prevention tips specifically for hostel environments
       - Self-care measures for students with limited resources
    3. Specific advice for hostelers to stay healthy in a shared living environment
    
    Format with clear sections and bullet points. Keep it practical for students living in hostels."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"{Fore.RED}⚠️  Error communicating with Gemini: {e}{Style.RESET_ALL}")
        return None

def display_seasonal_info():
    current_month = datetime.now().strftime('%B')
    location = "Hyderabad"
    
    print(f"\n{Fore.BLUE}🌡️ --- Seasonal Health Advisory for Hostel Students --- 🌡️{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}📅 Month: {current_month} | Location: {location}{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}" + "─" * 60 + f"{Style.RESET_ALL}")
    
    if USE_AI:
        print(f"{Fore.WHITE}Generating AI-powered seasonal health information...{Style.RESET_ALL}")
        ai_seasonal_info = get_ai_seasonal_info()
        
        if ai_seasonal_info:
            # Format AI output with color highlights
            formatted_info = ai_seasonal_info
            heading_pattern = r'(\d+\.\s+[\w\s]+:?|[\w\s]+:)'
            for match in re.finditer(heading_pattern, formatted_info):
                heading = match.group(0)
                formatted_info = formatted_info.replace(heading, f"{Fore.GREEN}{heading}{Style.RESET_ALL}", 1)
            
            keywords = ["symptoms", "prevention", "self-care", "advice", "warning", "alert", "caution", 
                        "important", "critical", "emergency", "doctor", "hospital", "clinic", "health center"]
            for keyword in keywords:
                formatted_info = re.sub(f'\\b{keyword}\\b', f"{Fore.YELLOW}{keyword}{Style.RESET_ALL}", 
                                        formatted_info, flags=re.IGNORECASE)
            
            print(formatted_info)
        else:
            display_hardcoded_seasonal_info(current_month, location)
    else:
        display_hardcoded_seasonal_info(current_month, location)

# Fallback information when AI is unavailable
def display_hardcoded_seasonal_info(current_month, location):
    print(f"{Fore.GREEN}1️⃣  Common Cold & Viral Flu:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   - Symptoms: Runny nose, cough, sore throat.")
    print(f"{Fore.WHITE}   - Tips: Rest, hydrate, gargle warm salt water.")
    print(f"{Fore.WHITE}   - {Fore.YELLOW}Hostel Tip: {Fore.WHITE}Keep your room ventilated and wash hands frequently.{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}2️⃣  Heat-Related Illnesses:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   - Symptoms: Dizziness, high temp, nausea.")
    print(f"{Fore.WHITE}   - Tips: Stay cool, drink electrolytes, avoid direct sun.")
    print(f"{Fore.WHITE}   - {Fore.YELLOW}Hostel Tip: {Fore.WHITE}Use wet towels to cool down if AC isn't available.{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}3️⃣  Waterborne Diseases (Monsoon Season):{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   - Symptoms: Vomiting, diarrhea, fever.")
    print(f"{Fore.WHITE}   - Tips: Drink safe water, avoid street food.")
    print(f"{Fore.WHITE}   - {Fore.YELLOW}Hostel Tip: {Fore.WHITE}Carry a water bottle with filtered water.{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}4️⃣  Allergies (Dust/Pollen):{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   - Symptoms: Sneezing, itchy eyes, rashes.")
    print(f"{Fore.WHITE}   - Tips: Stay indoors, use antihistamines if needed.")
    print(f"{Fore.WHITE}   - {Fore.YELLOW}Hostel Tip: {Fore.WHITE}Clean your room regularly to minimize dust.{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}5️⃣  Mosquito-Borne Diseases (Post-Monsoon):{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   - Symptoms: High fever, muscle pain, rash.")
    print(f"{Fore.WHITE}   - Tips: Use mosquito nets, repellents, remove stagnant water.")
    print(f"{Fore.WHITE}   - {Fore.YELLOW}Hostel Tip: {Fore.WHITE}Use mosquito repellent patches on windows.{Style.RESET_ALL}")
    
    print(f"\n{Fore.RED}⚠️  Note: Consult a doctor for serious symptoms.{Style.RESET_ALL}")

def main():
    try:
        print(f"{Fore.CYAN}Loading your personal health assistant...{Style.RESET_ALL}")
        while True:
            choice = display_menu()

            if choice == '1':
                handle_chat()
            elif choice == '2':
                view_logs()
            elif choice == '3':
                display_seasonal_info()
            elif choice == '4':
                print(f"\n{Fore.GREEN}👋 Thank you for using the Health & Well-being Bot. Stay safe and take care!{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}⚠️  Invalid choice. Please select between 1 and 4.{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n\n{Fore.GREEN}👋 Program exited. Take care!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()