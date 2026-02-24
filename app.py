import streamlit as st
import os
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables for Azure OpenAI
load_dotenv()

# Set up Page Config
st.set_page_config(
    page_title="A419 Sepsis Rationale Generator",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stTextArea>div>div>textarea {
        background-color: #ffffff;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .header-style {
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='header-style'>🏥 A419 Case Analysis & Rationale Generator</h1>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar for Navigation
with st.sidebar:
    st.markdown("### 🏥 DRG Audit Suite")
    page = st.selectbox("Select Diagnosis Code", ["A419 - Sepsis", "N179 - Acute Kidney Failure", "J9601 - Acute Respiratory Failure", "Other Codes (Coming Soon)"])
    st.divider()

# Main Interface
st.subheader(f"🔍 {page} Review")

# Layout for Analysis
col1, col2 = st.columns([1, 1])

if page == "A419 - Sepsis":
    with col1:
        st.subheader("❓ Clinical Questionnaire (Y/N)")
        
        is_ny_state = st.checkbox("Apply New York State Regulatory Requirements (SIRS focused)?")

        with st.expander("Sepsis-3 Organ Dysfunction Criteria", expanded=not is_ny_state):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                q_hypotension = st.radio("Fluid-unresponsive hypotension?", ("No", "Yes"), key="hypo")
                q_creatinine = st.radio("Acute Kidney Injury (Cr increase)?", ("No", "Yes"), key="crea")
                q_bilirubin = st.radio("Liver Dysfunction (Bilirubin)?", ("No", "Yes"), key="bili")
            with col_c2:
                q_platelets = st.radio("Thrombocytopenia/Coagulopathy?", ("No", "Yes"), key="plat")
                q_mental = st.radio("Altered Mental Status?", ("No", "Yes"), key="mental")
                q_lactate = st.radio("Lactic Acidosis?", ("No", "Yes"), key="lact")

        with st.expander("Infection Indicators", expanded=True):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                q_cultures = st.radio("Positive Blood Cultures?", ("No", "Yes"), key="cult")
            with col_i2:
                q_toxic = st.radio("Toxic/Acutely Ill Appearance?", ("No", "Yes"), key="toxic")

        # SIRS Criteria only enabled for NY State
        if is_ny_state:
            with st.expander("SIRS Criteria (NY State Requirement)", expanded=True):
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    q_wbc = st.radio("WBC > 12k or < 4k?", ("No", "Yes"), key="wbc")
                    q_temp = st.radio("Temp > 100.4F or < 96.8F?", ("No", "Yes"), key="temp")
                with col_s2:
                    q_hr = st.radio("Heart Rate > 90 bpm?", ("No", "Yes"), key="hr")
                    q_rr = st.radio("Respiratory Rate > 20 bpm?", ("No", "Yes"), key="rr")
        else:
            # Default values if hidden
            q_wbc = q_temp = q_hr = q_rr = "No (SIRS hidden)"

        with st.expander("Context & Differential"):
            q_alt_process = st.radio("Explainable by non-infectious process?", ("No", "Yes"), key="alt")
            alt_condition = st.text_input("Appropriate Principal Diagnosis (e.g., Aspiration, Diverticulosis, DKA):", key="alt_cond")

        st.subheader("🏁 Final Determination")
        q_final_decision = st.radio("Initial validation decision:", ("Denied", "Allowed"), key="final_a419")

    # Agent Data for A419
    answers = {
        "Diagnosis": "A419 - Sepsis",
        "NY State Rules": "Yes" if is_ny_state else "No",
        "Hypotension": q_hypotension,
        "AKI/Creatinine": q_creatinine,
        "Liver/Bilirubin": q_bilirubin,
        "Platelets": q_platelets,
        "Altered Mental Status": q_mental,
        "Lactate": q_lactate,
        "WBC Abnormality": q_wbc,
        "Temperature Abnormality": q_temp,
        "Positive Cultures": q_cultures,
        "Tachycardia": q_hr,
        "Tachypnea": q_rr,
        "Toxic Appearance": q_toxic,
        "Alternative Process": q_alt_process,
        "Specific Alternative": alt_condition,
        "User Decision": q_final_decision
    }
    
    agent_instructions = [
        "You are a Medical Documentation Expert specializing in DRG Validation for A419 (Sepsis).",
        f"The final decision is: {q_final_decision}. Your rationale MUST lead to this exact decision.",
        "Your output must be concise and follow this EXACT structure:",
        "1. RATIONALE SECTION: Start with the boiler-plate definition citing 'Third International Consensus Definitions'. Mention that SIRS is ubiquitous and non-specific.",
        "2. PATIENT SPECIFIC ANALYSIS: In 3-5 sentences, list the specific findings (or lack thereof) for this patient (e.g., mental status at baseline, normal platelets/creatinine, lactic acid non-specificity).",
        "3. CONCLUSION: End the rationale section with 'The coding of Sepsis is disallowed.' (or allowed).",
        "4. PDX SECTION: State 'The more appropriate principal diagnosis is [Condition].'",
        "Avoid any extra commentary. Keep it strictly to these sections."
    ]

elif page == "N179 - Acute Kidney Failure":
    with col1:
        st.subheader("❓ N179 Clinical Questionnaire")
        
        with st.expander("Creatinine & Renal Function", expanded=True):
            baseline_cr = st.text_input("Baseline Creatinine (mg/dL):", value="1.0")
            adm_cr = st.text_input("Admission/Nadir Creatinine (mg/dL):", value="1.3")
            peak_cr = st.text_input("Peak Creatinine during stay (mg/dL):", value="1.5")
            q_improvement = st.radio("Declined immediately with hydration?", ("No", "Yes"))

        with st.expander("Laboratory/Clinical Evidence"):
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                q_bun_cr = st.radio("High BUN/Cr ratio (e.g. > 20)?", ("No", "Yes"))
                q_u_na = st.radio("Low Urine Sodium / FENa < 1%?", ("No", "Yes"))
            with col_l2:
                q_sg = st.radio("High Urine Specific Gravity?", ("No", "Yes"))
                q_casts = st.radio("Granular/Muddy Casts present?", ("No", "Yes"))

        with st.expander("Alternative Causes"):
            q_dehydration = st.radio("Clinical Dehydration noted?", ("No", "Yes"))
            q_ckd = st.radio("History of CKD?", ("No", "Yes", "Stage 3", "Stage 4"))
            alt_pd_n179 = st.text_input("Appropriate Principal Diagnosis (e.g., Dehydration, Colitis):")

        st.subheader("🏁 Final Determination")
        q_final_decision = st.radio("Initial validation decision:", ("Denied", "Allowed"), key="final_n179")

    # Agent Data for N179
    answers = {
        "Diagnosis": "N179 - Acute Kidney Failure",
        "Baseline": baseline_cr,
        "Admission": adm_cr,
        "Peak": peak_cr,
        "Declined with Hydration": q_improvement,
        "High BUN/Cr": q_bun_cr,
        "Low Urine Na": q_u_na,
        "High SG": q_sg,
        "Granular Casts": q_casts,
        "Dehydration": q_dehydration,
        "CKD History": q_ckd,
        "Principal Diagnosis": alt_pd_n179,
        "User Decision": q_final_decision
    }

    agent_instructions = [
        "You are a Medical Documentation Expert specializing in DRG Validation for N179.",
        f"The final decision is: {q_final_decision}. Your rationale MUST lead to this exact decision.",
        "Your output must be concise and follow this EXACT structure:",
        "1. RATIONALE SECTION: Define AKI markers (1.5-fold or 0.3 increase). Briefly compare the patient's data (Baseline [Baseline] vs Peak [Peak]).",
        "2. ANALYSIS: Address the hydration response and specific labs (BUN/Cr, Na). State why it reflects hypovolemia rather than acute failure.",
        "3. CONCLUSION: End with 'Therefore, acute kidney failure is disallowed.'",
        "4. PDX SECTION: State 'The more appropriate principal diagnosis is [Condition].'",
        "Keep it professional and avoid wordiness."
    ]

elif page == "J9601 - Acute Respiratory Failure":
    with col1:
        st.subheader("❓ J9601 Clinical Questionnaire")
        
        with st.expander("Oxygenation & Baseline"):
            q_copd = st.radio("History of Chronic Lung Disease (COPD/Asthma)?", ("No", "Yes"))
            q_baseline_o2 = st.radio("Usually on home oxygen?", ("No", "Yes"))
            q_abg_obtained = st.radio("ABG obtained?", ("No", "Yes"))

        with st.expander("Clinical Presentation"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                q_distress = st.radio("Acute Distress / Tachypnea?", ("No", "Yes"))
                q_accessory = st.radio("Accessory Muscle Use?", ("No", "Yes"))
            with col_p2:
                q_conv_alert = st.radio("Patient 'Alert/Conversant' in notes?", ("No", "Yes"))
                q_o2_type = st.radio("Managed with:", ("Low-flow NC (1-4L)", "High-flow NC", "BiPAP/CPAP", "Intubation"))

        with st.expander("Differential & Course"):
            q_resolved_nebs = st.radio("Symptoms resolved with neb treatments?", ("No", "Yes"))
            q_resolved_diuresis = st.radio("Symptoms resolved with diuresis?", ("No", "Yes"))
            alt_pd_j96 = st.text_input("Appropriate Principal Diagnosis (e.g., COPD Exacerbation, Hypoxemia):")

        st.subheader("🏁 Final Determination")
        q_final_decision = st.radio("Initial validation decision:", ("Denied", "Allowed"), key="final_j96")

    # Agent Data for J9601
    answers = {
        "Diagnosis": "J9601 - Acute Respiratory Failure",
        "Chronic Lung": q_copd,
        "Home O2": q_baseline_o2,
        "ABG": q_abg_obtained,
        "Distress/Tachypnea": q_distress,
        "Accessory Muscle": q_accessory,
        "Alert/Conversant": q_conv_alert,
        "O2 Management": q_o2_type,
        "Resolved with Nebs": q_resolved_nebs,
        "Resolved with Diuresis": q_resolved_diuresis,
        "Principal Diagnosis": alt_pd_j96,
        "User Decision": q_final_decision
    }

    agent_instructions = [
        "You are a Medical Documentation Expert specializing in DRG Validation for J9601.",
        f"The final decision is: {q_final_decision}. Your rationale MUST lead to this exact decision.",
        "Your output must be concise and follow this EXACT structure:",
        "1. RATIONALE SECTION: Define hypoxic failure characteristics and mention 'degree of change from usual state'.",
        "2. ANALYSIS: Address O2 management (low flow NC) and lack of distress/accessory muscle use. Mention if ABG was missing.",
        "3. CONCLUSION: End with 'The diagnosis code J9601 is disallowed.'",
        "4. PDX SECTION: State 'The more appropriate principal diagnosis is [Condition].'",
        "Keep it short and analytical."
    ]

with col2:
    st.subheader("🤖 Generated Rationale")
    
    if st.button("Generate Rationale", type="primary"):
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

        if not (azure_endpoint and azure_api_key):
            st.error("Missing Azure Credentials in .env file.")
        else:
            with st.spinner("Synthesizing rationale..."):
                try:
                    # Initialize Agno Agent with dynamic instructions
                    agent = Agent(
                        model=AzureOpenAI(
                            id=azure_deployment,
                            api_key=azure_api_key,
                            azure_endpoint=azure_endpoint,
                        ),
                        instructions=agent_instructions,
                    )

                    prompt = f"""
                    TARGET DIAGNOSIS: {page}
                    CLINICAL FINDINGS:
                    {answers}

                    Generate a formal medical rationale based on these findings. 
                    - Focus on whether the documentation supports the diagnosis or if an alternative (like Dehydration, Aspiration, or CKD) is more accurate.
                    - Style: Professional, analytical, auditing tone.
                    - Sections: 'Rationale' and 'Decision'.
                    """

                    response = agent.run(prompt)
                    st.markdown(f"<div class='status-box'>{response.content}</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error generating rationale: {str(e)}")

st.markdown("---")
st.caption("Developed for A419 Case Review Automation using Agno & Azure OpenAI.")
