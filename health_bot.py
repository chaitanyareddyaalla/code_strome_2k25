import json
from datetime import datetime
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOG_FILE = os.getenv("LOG_FILE_NAME") or "health_log.json"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    USE_AI = True
else:
    print("Warning: GEMINI_API_KEY not found in .env file. Using rule-based suggestions.")
    USE_AI = False

def display_menu():
    print("\n✨ Welcome to your Personal Health & Well-being Bot! ✨")
    print("\nWhat would you like to do today?")
    print("1. Chat with the bot about how you're feeling.")
    print("2. View your previous health logs.")
    print("3. Learn about common seasonal illnesses and precautions in Hyderabad.")
    print("4. Exit.")
    choice = input("Enter your choice (1-4): ")
    return choice

def get_ai_suggestions(symptoms, mood):
    prompt = f"""The user reports the following physical symptoms: '{symptoms}'.
    Their current mood rating is {mood} out of 5.
    Based on this information, suggest 1-2 possible common health issues.
    Then, provide 2-3 concise and safe self-care or remedy advice, including mental well-being tips if the mood is low.
    Also, indicate if the user should consider consulting a doctor or seeking mental health support based on the symptoms and mood.
    Keep the language simple and easy for a hostel student to understand."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Error communicating with Gemini: {e}")
        return "Sorry, I couldn't get AI suggestions right now. Please try again later."

def get_rule_based_suggestions(symptoms, mood):
    possible_issues = []
    remedy_advice = []

    if "fever" in symptoms or "high temperature" in symptoms:
        possible_issues.append("Possible fever")
        remedy_advice.append("Stay hydrated, rest, and consider paracetamol if needed.")
        if "sore throat" in symptoms:
            possible_issues.append("Possible Common Cold or Viral Flu")
            remedy_advice.append("Gargle with warm salt water.")
    elif "headache" in symptoms:
        possible_issues.append("Possible headache")
        remedy_advice.append("Rest in a quiet place, stay hydrated.")
    elif "cough" in symptoms:
        possible_issues.append("Possible cough")
        remedy_advice.append("Try a cough syrup or home remedies like honey and lemon.")

    if mood <= 2:
        remedy_advice.append("Consider some relaxing activities like deep breathing or listening to calming music. If you've been feeling consistently low, consider reaching out to a friend, family member, or exploring mental health resources available at the hostel or nearby.")
    elif mood >= 4:
        remedy_advice.append("That's great to hear! Keep up the positive vibes and remember to take care of your well-being.")

    if "persistent" in symptoms or len(symptoms.split()) > 5 and "not improving" in symptoms:
        remedy_advice.append("⚠️ If your symptoms persist or worsen, please consult a doctor.")
    if mood == 1:
        remedy_advice.append("⚠️ If you've been feeling very low for an extended period, it's important to seek support. Consider talking to the hostel counselor or a mental health professional.")

    return {"possible_issues": ", ".join(possible_issues) or "No specific issue identified based on input.",
            "remedy_advice": "\n".join(remedy_advice) or "No specific remedy suggested."}

def handle_chat():
    print("\n🗣️ Let's chat about how you're feeling today.")
    physical_symptoms = input("Please describe any physical symptoms you're experiencing (e.g., fever, headache): ").strip().lower()
    while True:
        mood_str = input("On a scale of 1 to 5 (1 being very low, 5 being excellent), how would you rate your current mood? ")
        if mood_str.isdigit() and 1 <= int(mood_str) <= 5:
            mood_rating = int(mood_str)
            break
        else:
            print("⚠️ Invalid mood rating. Please enter a number between 1 and 5.")

    if USE_AI:
        ai_suggestions = get_ai_suggestions(physical_symptoms, mood_rating)
        print("\n🤖 AI-Powered Suggestions:")
        print(ai_suggestions)
        suggestions_to_log = {"possible_issues": "AI Generated", "remedy_advice": ai_suggestions}
    else:
        rule_based_suggestions = get_rule_based_suggestions(physical_symptoms, mood_rating)
        print("\n💡 Here are some suggestions based on your input:")
        print("Possible Issue(s):", rule_based_suggestions['possible_issues'])
        print("Remedy/Advice:", rule_based_suggestions['remedy_advice'])
        suggestions_to_log = rule_based_suggestions

    save_log = input("💾 Do you want to save this log? (yes/no): ").strip().lower()
    if save_log == 'yes':
        save_to_log(physical_symptoms, mood_rating, suggestions_to_log)
        print("✅ Log Saved Successfully.")
    else:
        print("❌ Log not saved.")

def save_to_log(symptoms, mood, suggestions):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "physical_symptoms": symptoms,
        "mood_rating": mood,
        "possible_issues": suggestions['possible_issues'],
        "remedy_advice": suggestions['remedy_advice']
    }
    try:
        with open(LOG_FILE, 'r+') as f:
            data = json.load(f)
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=4)
    except FileNotFoundError:
        with open(LOG_FILE, 'w') as f:
            json.dump([log_entry], f, indent=4)
    except json.JSONDecodeError:
        with open(LOG_FILE, 'w') as f:
            json.dump([log_entry], f, indent=4)

def view_logs():
    print("\n📜 --- Your Previous Health Logs --- 📜")
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
            if not data:
                print("No logs available yet.")
            else:
                for entry in data:
                    print(f"\n🗓️ Timestamp: {entry['timestamp']}")
                    print(f"🤕 Physical Symptoms: {entry['physical_symptoms']}")
                    print(f"😊 Mood Rating: {entry['mood_rating']}")
                    print(f"🤔 Possible Issue(s): {entry['possible_issues']}")
                    print(f"💊 Remedy/Advice: {entry['remedy_advice']}")
    except FileNotFoundError:
        print("No logs available yet.")
    except json.JSONDecodeError:
        print("⚠️ Error reading log file.")

def display_seasonal_info():
    print("\n🌡️ --- Common Seasonal Illnesses and Precautions in Hyderabad --- 🌡️")
    print(f"\nBased on the current time ({datetime.now().strftime('%B')} in Hyderabad), here are some common concerns:")
    print("\n1. Common Cold and Viral Flu:")
    print("   - Symptoms: Runny nose, sore throat, cough, sneezing, mild fever.")
    print("   - First Aid: Rest, stay hydrated, gargle with warm salt water.")
    print("   - Precautions: Maintain hygiene, avoid close contact with infected individuals.")
    print("\n2. Heat-Related Illnesses (Heatstroke, Heat Exhaustion):")
    print("   - Symptoms: High body temperature, headache, dizziness, nausea, rapid pulse, excessive sweating or lack thereof.")
    print("   - First Aid: Move to a cool place, drink water with electrolytes, cool the body with damp cloths or ice packs, seek medical help for heatstroke.")
    print("   - Precautions: Stay hydrated, avoid prolonged exposure to direct sunlight, wear light and loose clothing, use sunscreen.")
    print("\n3. Waterborne Diseases (if monsoon season is near):")
    print("   - Symptoms (vary): Diarrhea, vomiting, abdominal pain, fever.")
    print("   - First Aid: Stay hydrated with clean water and oral rehydration solutions, seek medical attention.")
    print("   - Precautions: Drink boiled or treated water, maintain food hygiene, avoid street food from unhygienic places.")
    print("\n4. Allergies (Dust, Pollen, Humidity):")
    print("   - Symptoms: Sneezing, runny nose, itchy eyes, skin rashes, difficulty breathing.")
    print("   - First Aid: Avoid known allergens, use over-the-counter antihistamines if needed, consult a doctor for severe reactions.")
    print("   - Precautions: Keep living spaces clean, use air purifiers, avoid outdoor activities during high pollen counts.")
    print("\n5. Mosquito-Borne Diseases (Dengue, Malaria - especially post-monsoon):")
    print("   - Symptoms (vary): High fever, headache, joint and muscle pain, rash, chills.")
    print("   - First Aid: Rest, drink fluids, seek medical attention for diagnosis and treatment.")
    print("   - Precautions: Use mosquito repellents, wear long sleeves and pants, use mosquito nets, prevent water stagnation around the hostel.")
    print("\n⚠️ Remember, this information is for general awareness. Consult a doctor for specific health concerns. ⚠️")

def main():
    while True:
        choice = display_menu()

        if choice == '1':
            handle_chat()
        elif choice == '2':
            view_logs()
        elif choice == '3':
            display_seasonal_info()
        elif choice == '4':
            print("\n👋 Thank you for using the Health & Well-being Bot. Stay healthy and take care! 👋")
            break
        else:
            print("⚠️ Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()