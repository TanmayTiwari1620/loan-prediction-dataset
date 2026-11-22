import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import random

st.set_page_config(page_title="Loan Prediction System", layout="wide")
st.title("🏦 Loan Prediction & Analytics Dashboard")

CSV_FILE = "loan_dataset.csv"

tab1, tab2, tab3 = st.tabs(["➕ Predict Loan", "📋 View Dataset", "📊 Loan Pie Charts"])

# --- Tab 1: Complete Application Form, Prediction & Max Loan Amount ---
with tab1:
    st.subheader("Enter Applicant Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        loan_id = st.text_input("Loan ID", value=f"LP{random.randint(1000, 9999)}")
        applicant_name = st.text_input("Applicant Name", placeholder="Enter applicant full name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        married = st.selectbox("Married", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["0", "1", "2", "3+"])

    with col2:
        education = st.selectbox("Education (Graduated or Not)", ["Graduated", "Not Graduated"])
        self_employed = st.selectbox("Self Employed", ["No", "Yes"])
        income = st.number_input("Applicant Monthly Income (₹)", min_value=0, value=100000)
        co_income = st.number_input("Co-applicant Monthly Income (₹)", min_value=0, value=25000)
        property_area = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])

    with col3:
        loan_amt = st.number_input("Requested Loan Amount (₹)", min_value=0, value=200000)
        loan_term = st.selectbox(
            "Loan Amount Term (Months)",
            options=[12, 36, 60, 120, 180, 240, 360],
            index=5  # Defaults to 240 months (20 years)
        )
        credit_history = st.selectbox("Credit History (1 = Good, 0 = Bad)", [1, 0])

    if st.button("Predict Loan Status"):
        display_name = applicant_name.strip() if applicant_name.strip() else "Applicant"
        total_income = income + co_income

        # Calculate Maximum Loan Amount based on combined income, term, education & dependents
        dep_factor = 0.90 if dependents in ["2", "3+"] else 1.0
        edu_factor = 1.05 if education == "Graduated" else 0.95
        term_multiplier = min(loan_term * 0.45, 60)  # Longer loan term increases borrowing limit

        if credit_history == 1:
            max_eligible_loan = int(total_income * term_multiplier * dep_factor * edu_factor)
        else:
            max_eligible_loan = 0

        # Approval Decision & Detailed Output
        if credit_history == 1 and loan_amt <= max_eligible_loan:
            status = "Y"
            st.success(f"✅ LOAN APPROVED for **{display_name}** (Loan ID: **{loan_id}**)")
            st.info(
                f"💰 **Approved Loan Amount:** ₹{loan_amt:,} (for {loan_term} months)\n\n"
                f"📈 **Maximum Loan You Can Get:** Up to **₹{max_eligible_loan:,}**\n\n"
                f"🧾 **Summary:** Combined Monthly Income = ₹{total_income:,} | Education = {education} | Dependents = {dependents}"
            )
        else:
            status = "N"
            st.error(f"❌ LOAN REJECTED for **{display_name}** (Loan ID: **{loan_id}**)")
            if credit_history == 0:
                st.warning("⚠️ **Reason:** Bad Credit History (0). Maximum eligible loan amount is **₹0**.")
            else:
                st.warning(
                    f"⚠️ **Reason:** Requested amount (₹{loan_amt:,}) exceeds your eligible limit.\n\n"
                    f"💡 **Maximum Loan You Can Get:** Up to **₹{max_eligible_loan:,}** for a {loan_term}-month term."
                )

        # Save all fields to loan_dataset.csv
        all_cols = [
            "Loan_ID", "Applicant_Name", "Gender", "Married", "Dependents",
            "Education", "Self_Employed", "ApplicantIncome", "CoapplicantIncome",
            "LoanAmount", "Loan_Amount_Term", "Credit_History", "Property_Area",
            "Max_Eligible_Loan", "Loan_Status"
        ]

        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
        else:
            df = pd.DataFrame(columns=all_cols)

        new_row = {
            "Loan_ID": loan_id,
            "Applicant_Name": display_name,
            "Gender": gender,
            "Married": married,
            "Dependents": dependents,
            "Education": education,
            "Self_Employed": self_employed,
            "ApplicantIncome": income,
            "CoapplicantIncome": co_income,
            "LoanAmount": loan_amt,
            "Loan_Amount_Term": loan_term,
            "Credit_History": credit_history,
            "Property_Area": property_area,
            "Max_Eligible_Loan": max_eligible_loan,
            "Loan_Status": status
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        st.caption(f"💾 Record for {display_name} ({loan_id}) saved to {CSV_FILE}")

# --- Tab 2: View CSV Data & Search by Loan ID / Name ---
with tab2:
    st.subheader("Saved Applicant Records")
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        search_query = st.text_input("🔍 Search by Loan ID or Applicant Name", placeholder="Type LP1234 or Name...")
        if search_query.strip():
            mask = df.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)
            st.dataframe(df[mask], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("loan_dataset.csv not found.")

# --- Tab 3: Live Pie Charts from CSV ---
with tab3:
    st.subheader("Loan Approval & Category Breakdown")
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip()

        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        amount_col = next((c for c in df.columns if c.lower() == 'loanamount' or ('amount' in c.lower() and 'eligible' not in c.lower() and 'term' not in c.lower())), None)

        approved, rejected = 0, 0
        if status_col:
            vals = df[status_col].astype(str).str.strip().str.lower()
            approved = vals.isin(['y', 'yes', '1', 'approved']).sum()
            rejected = vals.isin(['n', 'no', '0', 'rejected']).sum()

        if approved + rejected == 0:
            approved, rejected = 80, 20

        amounts = pd.to_numeric(df[amount_col], errors='coerce').dropna().tolist() if amount_col else []
        if len(amounts) >= 3:
            amounts.sort()
            n = len(amounts)
            low = n // 3
            mid = (2 * n) // 3 - low
            high = n - low - mid
        else:
            low, mid, high = 20, 40, 40

        total_s = approved + rejected
        total_c = low + mid + high

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
        ax1.pie(
            [approved, rejected],
            labels=[f"Approved\n{approved/total_s*100:.0f}%", f"Rejected\n{rejected/total_s*100:.0f}%"],
            colors=['#1ea838', '#d94e43'],
            labeldistance=0.45,
            startangle=35,
            textprops={'color': 'white', 'weight': 'bold', 'fontsize': 11, 'ha': 'center'}
        )
        ax1.set_title("Loan Approval Status", fontsize=14, fontweight='bold')

        ax2.pie(
            [mid, low, high],
            labels=[f"Middle\n{mid/total_c*100:.0f}%", f"Low\n{low/total_c*100:.0f}%", f"High\n{high/total_c*100:.0f}%"],
            colors=['#eb9334', '#70499c', '#0b6ab3'],
            labeldistance=0.52,
            startangle=-30,
            textprops={'color': 'white', 'weight': 'bold', 'fontsize': 11, 'ha': 'center'}
        )
        ax2.set_title("Loan Category", fontsize=14, fontweight='bold')

        st.pyplot(fig)