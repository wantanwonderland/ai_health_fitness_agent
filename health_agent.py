import streamlit as st
import asyncio
import nest_asyncio
from agno.agent import Agent
from agno.models.google import Gemini
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

st.set_page_config(
    page_title="AI Health & Fitness Planner",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fffaf0;
        border: 1px solid #fbd38d;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

def display_dietary_plan(plan_content):
    with st.expander("📋 Your Personalized Dietary Plan", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Why this plan works")
            st.info(plan_content.get("why_this_plan_works", "Information not available"))
            st.markdown("### 🍽️ Meal Plan")
            st.write(plan_content.get("meal_plan", "Plan not available"))
        
        with col2:
            st.markdown("### ⚠️ Important Considerations")
            considerations = plan_content.get("important_considerations", "").split('\n')
            for consideration in considerations:
                if consideration.strip():
                    st.warning(consideration)

def display_fitness_plan(plan_content):
    with st.expander("💪 Your Personalized Fitness Plan", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Goals")
            st.success(plan_content.get("goals", "Goals not specified"))
            st.markdown("### 🏋️‍♂️ Exercise Routine")
            st.write(plan_content.get("routine", "Routine not available"))
        
        with col2:
            st.markdown("### 💡 Pro Tips")
            tips = plan_content.get("tips", "").split('\n')
            for tip in tips:
                if tip.strip():
                    st.info(tip)

def main():
    # Set up a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if 'dietary_plan' not in st.session_state:
        st.session_state.dietary_plan = {}
        st.session_state.fitness_plan = {}
        st.session_state.qa_pairs = []
        st.session_state.plans_generated = False

    st.title("🏋️‍♂️ AI Health & Fitness Planner")
    st.markdown("""
        <div style='background-color: #0000; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
        Get personalized dietary and fitness plans tailored to your goals and preferences.
        Our AI-powered system considers your unique profile to create the perfect plan for you.
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("🔑 API Configuration")
        gemini_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Gemini API key to access the service"
        )
        
        if not gemini_api_key:
            st.warning("⚠️ Please enter your Gemini API Key to proceed")
            st.markdown("[Get your API key here](https://aistudio.google.com/apikey)")
            return
        
        st.success("API Key accepted!")

    # Language selector
    st.header("🌐 Language Settings")
    languages = ["English", "Bahasa Malaysia", "Mandarin", "Tamil", "Japanese", "Korean"]
    selected_language = st.selectbox("Select your preferred language", options=languages)
    
    # Store language preference in session state
    if 'language' not in st.session_state or st.session_state.language != selected_language:
        st.session_state.language = selected_language
        st.success(f"Language set to {selected_language}")

    if gemini_api_key:
        try:
            gemini_model = Gemini(id="gemini-1.5-flash", api_key=gemini_api_key)
        except Exception as e:
            st.error(f"❌ Error initializing Gemini model: {e}")
            return

        st.header("👤 Your Profile")
        
        # Create tabs for better organization of profile information
        tabs = st.tabs(["Basic Information", "Health Details", "Location & Lifestyle"])
        
        # Tab 1: Basic Information
        with tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                age = st.number_input("Age", min_value=10, max_value=100, step=1, help="Enter your age")
                height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.1)
                weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
            
            with col2:
                sex = st.selectbox("Sex", options=["Male", "Female", "Other"])
                ethnicity = st.selectbox(
                    "Ethnicity/Cultural Background", 
                    options=["Malay", "Chinese", "Indian", "Indigenous", "Other Asian", "Western", "Other"],
                    help="Select your cultural background for culturally appropriate recommendations"
                )
                fitness_goals = st.selectbox(
                    "Fitness Goals",
                    options=["Lose Weight", "Gain Muscle", "Endurance", "Stay Fit", "Strength Training", "Manage Medical Conditions"],
                    help="What do you want to achieve?"
                )
        
        # Tab 2: Health Details
        with tabs[1]:
            col1, col2 = st.columns(2)
            
            with col1:
                activity_level = st.selectbox(
                    "Activity Level",
                    options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                    help="Choose your typical activity level"
                )
                medical_conditions = st.multiselect(
                    "Medical Conditions",
                    options=["None", "Diabetes", "Hypertension", "Heart Disease", "Arthritis", "Osteoporosis", "Obesity", "Other"],
                    default=["None"],
                    help="Select any medical conditions you have"
                )
                if "Other" in medical_conditions:
                    other_conditions = st.text_input("Please specify other medical conditions")
            
            with col2:
                dietary_preferences = st.selectbox(
                    "Dietary Preferences",
                    options=["No Restrictions", "Vegetarian", "Vegan", "Keto", "Gluten Free", "Low Carb", "Dairy Free", "Halal", "Kosher"],
                    help="Select your dietary preference"
                )
                food_allergies = st.multiselect(
                    "Food Allergies",
                    options=["None", "Nuts", "Shellfish", "Dairy", "Eggs", "Wheat", "Soy", "Other"],
                    default=["None"],
                    help="Select any food allergies you have"
                )
                if "Other" in food_allergies:
                    other_allergies = st.text_input("Please specify other allergies")
        
        # Tab 3: Location & Lifestyle
        with tabs[2]:
            col1, col2 = st.columns(2)
            
            with col1:
                region = st.selectbox(
                    "Region",
                    options=["Selangor", "Kuala Lumpur", "Penang", "Johor", "Sabah", "Sarawak", "Other Malaysian State", "Other Country"],
                    help="Select your region for location-specific advice"
                )
                if region == "Other Malaysian State":
                    other_state = st.text_input("Please specify which Malaysian state")
                elif region == "Other Country":
                    other_country = st.text_input("Please specify which country")
                
                living_environment = st.selectbox(
                    "Living Environment",
                    options=["Urban City", "Suburban", "Rural/Kampung", "Coastal Area"],
                    help="Select your living environment"
                )
            
            with col2:
                equipment_access = st.multiselect(
                    "Equipment Access",
                    options=["None", "Basic Home Equipment", "Full Gym", "Outdoor Spaces", "Community Center", "Traditional Tools"],
                    default=["None"],
                    help="What exercise equipment do you have access to?"
                )
                lifestyle_factors = st.multiselect(
                    "Lifestyle Factors",
                    options=["Desk Job", "Physical Work", "Frequent Travel", "Limited Mobility", "Caregiver", "Night Shift Worker"],
                    help="Select factors that affect your daily routine"
                )

        if st.button("🎯 Generate My Personalized Plan", use_container_width=True):
            with st.spinner("Creating your perfect health and fitness routine..."):
                try:
                    # Prepare medical conditions string, handling "None" and "Other" properly
                    final_medical_conditions = []
                    for condition in medical_conditions:
                        if condition == "None" and len(medical_conditions) > 1:
                            continue  # Skip "None" if other conditions are selected
                        elif condition == "Other" and 'other_conditions' in locals():
                            final_medical_conditions.append(other_conditions)
                        else:
                            final_medical_conditions.append(condition)
                    
                    # Prepare allergies string, handling "None" and "Other" properly
                    final_food_allergies = []
                    for allergy in food_allergies:
                        if allergy == "None" and len(food_allergies) > 1:
                            continue  # Skip "None" if other allergies are selected
                        elif allergy == "Other" and 'other_allergies' in locals():
                            final_food_allergies.append(other_allergies)
                        else:
                            final_food_allergies.append(allergy)
                    
                    # Process region information
                    final_region = region
                    if region == "Other Malaysian State" and 'other_state' in locals():
                        final_region = other_state
                    elif region == "Other Country" and 'other_country' in locals():
                        final_region = other_country

                    # Include language in agent instructions
                    dietary_agent = Agent(
                        name="Dietary Expert",
                        role="Provides personalized dietary recommendations",
                        model=gemini_model,
                        instructions=[
                            f"Provide all responses in {st.session_state.language}.",
                            "Consider the user's input, including dietary restrictions, medical conditions, and cultural background.",
                            "For diabetic users, focus on low glycemic index foods and proper meal timing.",
                            "Include locally available ingredients based on the user's region and living environment.",
                            "For users in rural/kampung areas, suggest recipes using locally grown produce and traditional cooking methods.",
                            "Respect cultural and religious dietary practices relevant to the user's background.",
                            "Suggest a detailed meal plan for the day, including breakfast, lunch, dinner, and snacks.",
                            "Provide specific portion guidance for users with medical conditions like diabetes.",
                            "Provide a brief explanation of why the plan is suited to the user's goals and medical needs.",
                        ]
                    )

                    fitness_agent = Agent(
                        name="Fitness Expert",
                        role="Provides personalized fitness recommendations",
                        model=gemini_model,
                        instructions=[
                            f"Provide all responses in {st.session_state.language}.",
                            "Provide exercises tailored to the user's goals, age, medical conditions, and living environment.",
                            "For older users, focus on low-impact exercises that improve balance and strength.",
                            "For users with diabetes, suggest appropriate exercise intensity and timing around meals.",
                            "Consider available resources in rural/kampung settings - suggest exercises that don't require gym equipment.",
                            "Include culturally relevant physical activities when appropriate.",
                            "Design exercises around the equipment the user has access to.",
                            "Include warm-up, main workout, and cool-down exercises suitable for the user's profile.",
                            "Explain the benefits of each recommended exercise for their specific conditions.",
                        ]
                    )


                    user_profile = f"""
                    Age: {age}
                    Weight: {weight}kg
                    Height: {height}cm
                    Sex: {sex}
                    Ethnicity: {ethnicity}
                    Activity Level: {activity_level}
                    Dietary Preferences: {dietary_preferences}
                    Food Allergies: {', '.join(final_food_allergies)}
                    Fitness Goals: {fitness_goals}
                    Medical Conditions: {', '.join(final_medical_conditions)}
                    Region: {final_region}
                    Living Environment: {living_environment}
                    Equipment Access: {', '.join(equipment_access)}
                    Lifestyle Factors: {', '.join(lifestyle_factors)}
                    Preferred Language: {st.session_state.language}
                    """

                    dietary_plan_response = dietary_agent.run(user_profile)
                    dietary_plan = {
                        "why_this_plan_works": "Personalized nutrition based on your profile, medical needs, and cultural background",
                        "meal_plan": dietary_plan_response.content,
                        "important_considerations": """
                        - Hydration: Drink plenty of water throughout the day
                        - Electrolytes: Monitor sodium, potassium, and magnesium levels
                        - Fiber: Ensure adequate intake through vegetables and fruits
                        - Listen to your body: Adjust portion sizes as needed
                        - For medical conditions: Always consult with your healthcare provider
                        """
                    }

                    fitness_plan_response = fitness_agent.run(user_profile)
                    fitness_plan = {
                        "goals": f"Personalized exercise plan for {age} year old {ethnicity} {sex.lower()} with {', '.join(final_medical_conditions)} living in {living_environment}",
                        "routine": fitness_plan_response.content,
                        "tips": """
                        - Track your progress regularly
                        - Allow proper rest between workouts
                        - Focus on proper form
                        - Stay consistent with your routine
                        - Adapt exercises based on how you feel each day
                        """
                    }
                    
                    # Store the profile in session state
                    st.session_state.user_profile = user_profile

                    st.session_state.dietary_plan = dietary_plan
                    st.session_state.fitness_plan = fitness_plan
                    st.session_state.plans_generated = True
                    st.session_state.qa_pairs = []

                    display_dietary_plan(dietary_plan)
                    display_fitness_plan(fitness_plan)

                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

        if st.session_state.plans_generated:
            st.header("❓ Questions about your plan?")
            
            # Enhanced Q&A section with categories
            question_categories = ["Diet", "Exercise", "Medical Considerations", "Cultural Adaptations", "Local Ingredients"]
            selected_category = st.selectbox("Question category", options=question_categories)
            
            question_input = st.text_input(f"What would you like to know about your {selected_category.lower()}?")

            if st.button("Get Answer"):
                if question_input:
                    with st.spinner("Finding the best answer for you..."):
                        dietary_plan = st.session_state.dietary_plan
                        fitness_plan = st.session_state.fitness_plan

                        context = f"Dietary Plan: {dietary_plan.get('meal_plan', '')}\n\nFitness Plan: {fitness_plan.get('routine', '')}"
                        full_context = f"{context}\nQuestion Category: {selected_category}\nUser Question: {question_input}"

                        try:
                            agent = Agent(model=gemini_model, show_tool_calls=True, markdown=True)
                            run_response = agent.run(full_context)

                            if hasattr(run_response, 'content'):
                                answer = run_response.content
                            else:
                                answer = "Sorry, I couldn't generate a response at this time."

                            st.session_state.qa_pairs.append((question_input, answer))
                        except Exception as e:
                            st.error(f"❌ An error occurred while getting the answer: {e}")

            if st.session_state.qa_pairs:
                with st.expander("💬 Q&A History", expanded=True):
                    for i, (question, answer) in enumerate(st.session_state.qa_pairs):
                        st.markdown(f"**Q{i+1}:** {question}")
                        st.markdown(f"**A{i+1}:** {answer}")
                        st.divider()
            
    # Plan export option
    st.header("📤 Export Your Plans")
    export_format = st.radio("Export format", ["PDF", "Text"])
    # In the export section
    if st.button("Export Plans"):
        try:
            if "user_profile" not in st.session_state:
                st.error("Please generate your plan first before exporting")
                return
                
            # Use the stored profile
            user_profile = st.session_state.user_profile
            
            # Generate appropriate format
            if export_format == "PDF":
                buffer = create_plan_pdf(st.session_state.dietary_plan, st.session_state.fitness_plan, user_profile)
                mime_type = "application/pdf"
                file_extension = "pdf"
            else:  # Text format
                content = create_plan_text(st.session_state.dietary_plan, st.session_state.fitness_plan, user_profile)
                buffer = io.BytesIO(content.encode())
                mime_type = "text/plain"
                file_extension = "txt"
            
            st.success("Your personalized health and fitness plans are ready for download!")
            st.download_button(
                "Download Your Plans",
                data=buffer,
                file_name=f"health_fitness_plan.{file_extension}",
                mime=mime_type
            )
        except Exception as e:
            st.error(f"❌ Error creating download file: {e}")


def create_plan_text(dietary_plan, fitness_plan, user_profile):
    """Format plans as plain text"""
    text_content = "=== YOUR PERSONALIZED HEALTH & FITNESS PLAN ===\n\n"
    
    # Add user profile summary
    text_content += "=== USER PROFILE ===\n"
    for line in user_profile.strip().split("\n"):
        if line.strip():
            text_content += f"{line.strip()}\n"
    
    # Add dietary plan
    text_content += "\n\n=== DIETARY PLAN ===\n"
    text_content += f"\nWHY THIS PLAN WORKS:\n{dietary_plan.get('why_this_plan_works', '')}\n"
    text_content += f"\nMEAL PLAN:\n{dietary_plan.get('meal_plan', '')}\n"
    text_content += "\nIMPORTANT CONSIDERATIONS:\n"
    for consideration in dietary_plan.get('important_considerations', '').split('\n'):
        if consideration.strip():
            text_content += f"- {consideration.strip()}\n"
    
    # Add fitness plan
    text_content += "\n\n=== FITNESS PLAN ===\n"
    text_content += f"\nGOALS:\n{fitness_plan.get('goals', '')}\n"
    text_content += f"\nEXERCISE ROUTINE:\n{fitness_plan.get('routine', '')}\n"
    text_content += "\nPRO TIPS:\n"
    for tip in fitness_plan.get('tips', '').split('\n'):
        if tip.strip():
            text_content += f"- {tip.strip()}\n"
    
    return text_content

def create_plan_pdf(dietary_plan, fitness_plan, user_profile):
    """Create a PDF document with formatted plans"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceAfter=6
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.darkslateblue,
        spaceAfter=6
    )
    
    # Build the document content
    elements = []
    
    # Title
    elements.append(Paragraph("Your Personalized Health & Fitness Plan", title_style))
    elements.append(Spacer(1, 12))
    
    # User Profile
    elements.append(Paragraph("User Profile", heading_style))
    
    # Format profile as table
    profile_data = []
    for line in user_profile.strip().split("\n"):
        if line.strip():
            key_value = line.strip().split(":", 1)
            if len(key_value) == 2:
                profile_data.append([key_value[0].strip(), key_value[1].strip()])
    
    if profile_data:
        profile_table = Table(profile_data, colWidths=[150, 350])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        elements.append(profile_table)
    
    elements.append(Spacer(1, 20))
    
    # Dietary Plan
    elements.append(Paragraph("Dietary Plan", heading_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("Why This Plan Works", subheading_style))
    elements.append(Paragraph(dietary_plan.get('why_this_plan_works', ''), styles['Normal']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("Meal Plan", subheading_style))
    elements.append(Paragraph(dietary_plan.get('meal_plan', ''), styles['Normal']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("Important Considerations", subheading_style))
    for consideration in dietary_plan.get('important_considerations', '').split('\n'):
        if consideration.strip():
            elements.append(Paragraph(f"• {consideration.strip()}", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # Fitness Plan
    elements.append(Paragraph("Fitness Plan", heading_style))
    elements.append(Spacer(1, 6))
    
    elements.append(Paragraph("Goals", subheading_style))
    elements.append(Paragraph(fitness_plan.get('goals', ''), styles['Normal']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("Exercise Routine", subheading_style))
    elements.append(Paragraph(fitness_plan.get('routine', ''), styles['Normal']))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("Pro Tips", subheading_style))
    for tip in fitness_plan.get('tips', '').split('\n'):
        if tip.strip():
            elements.append(Paragraph(f"• {tip.strip()}", styles['Normal']))
    
    # Build the PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    main()

