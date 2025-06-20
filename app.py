import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os
import tempfile

try:
    # Debug print
    print(f"Current Directory: {os.getcwd()}")
    print(f"Available Files: {os.listdir()}")

    # Load data
    df = pd.read_csv("strict_filtered_species_data.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Check required column
    if "common_name" not in df.columns:
        st.error("Missing 'common_name' column in dataset.")
        st.stop()

    required_cols = ["avg_dbh_growth", "carbon_fraction", "survival_rate"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    df = df.dropna(subset=["common_name"] + required_cols)
    indian_tree_species = sorted(df["common_name"].dropna().unique())

    if not indian_tree_species:
        st.error("No valid species in dataset.")
        st.stop()

    indian_cities = [
        "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow",
        "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Kalyan", "Vasai", "Varanasi", "Srinagar", "Ranchi", "Amritsar", "Jodhpur", "Coimbatore"
    ]

    # UI
    st.title("🌳 Tree CO₂ Sequestration Comparator (India)")

    city = st.selectbox("📍 Select Your City (India Only)", indian_cities)
    species = st.selectbox("🌱 Choose a Tree Species (India Only)", indian_tree_species)
    nickname = st.text_input("Give a Nickname to Your Tree", "My Tree")
    years = st.slider("⏳ Years to Estimate CO₂", 1, 50, 20)
    num_trees = st.number_input("🌲 Number of Trees", min_value=1, value=10)

    tree_data = df[df["common_name"] == species]
    if tree_data.empty:
        st.error("Species data not found.")
        st.stop()

    tree_data = tree_data.iloc[0]

    def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees):
        try:
            dbh = max(0, growth_rate * years)
            biomass = 0.25 * (dbh ** 2) * years
            carbon = biomass * carbon_fraction
            co2 = carbon * 3.67
            return (co2 * survival_rate * num_trees) / 1000
        except Exception as calc_err:
            print(f"Error in CO2 calculation: {calc_err}")
            return 0

    user_co2 = calculate_co2(tree_data["avg_dbh_growth"], tree_data["carbon_fraction"], tree_data["survival_rate"], years, num_trees)
    st.success(f"✅ Your Tree ({species}) will sequester: **{user_co2:.2f} metric tons** of CO₂ in {years} years.")

    # AI Suggestion
    ai_df = df[df["common_name"] != species].copy()
    ai_df["estimated_co2"] = ai_df.apply(lambda row: calculate_co2(
        row["avg_dbh_growth"], row["carbon_fraction"], row["survival_rate"], years, num_trees), axis=1)

    better_ai = ai_df[ai_df["estimated_co2"] > user_co2]
    if not better_ai.empty:
        try:
            ai_best = better_ai.sort_values("estimated_co2", ascending=False).iloc[0]
            ai_species = ai_best["common_name"]
            ai_co2 = ai_best["estimated_co2"]
            st.info(f"🤖 AI Suggests: {ai_species}")
            st.success(f"💡 AI Tree CO₂ Estimate: **{ai_co2:.2f} metric tons**")
        except IndexError as e:
            st.warning("⚠️ Unexpected error during AI suggestion.")
            ai_species = None
            ai_co2 = 0
    else:
        ai_species = None
        ai_co2 = 0
        st.warning("⚠️ No better tree found by AI.")

    # Chart
    def generate_chart(user_co2, ai_co2):
        fig, ax = plt.subplots()
        ax.bar(["Your Tree", "AI Tree"], [user_co2, ai_co2], color=["green", "blue"])
        ax.set_ylabel("CO₂ Sequestered (metric tons)")
        ax.set_title("User vs AI Tree CO₂ Comparison")
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf

    chart_img = generate_chart(user_co2, ai_co2)
    st.image(chart_img, caption="User vs AI Tree CO₂", use_container_width=True)

    # PDF generation
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()

        font_path_regular = os.path.join(os.getcwd(), 'DejaVuSans.ttf')
        font_path_bold = os.path.join(os.getcwd(), 'DejaVuSans-Bold.ttf')

        pdf.add_font('DejaVuSans', '', font_path_regular, uni=True)
        pdf.add_font('DejaVuSans', 'B', font_path_bold, uni=True)

        pdf.set_font("DejaVuSans", "B", 16)
        pdf.cell(190, 10, "Tree CO₂ Comparison Report", ln=True, align='C')
        pdf.set_font("DejaVuSans", "", 12)
        pdf.ln(10)
        pdf.cell(190, 10, f"📍 City: {city}", ln=True)
        pdf.cell(190, 10, f"🌿 Your Tree: {species} (Nickname: {nickname})", ln=True)
        pdf.cell(190, 10, f"Years: {years}", ln=True)
        pdf.cell(190, 10, f"Number of Trees: {num_trees}", ln=True)
        pdf.cell(190, 10, f"Estimated CO₂: {user_co2:.2f} metric tons", ln=True)
        if ai_species:
            pdf.cell(190, 10, f"🤖 AI Tree: {ai_species}", ln=True)
            pdf.cell(190, 10, f"AI CO₂ Estimate: {ai_co2:.2f} metric tons", ln=True)
        else:
            pdf.cell(190, 10, "No better tree recommended by AI.", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(chart_img.getbuffer())
            image_path = tmp_file.name
        try:
            pdf.image(image_path, x=10, w=180)
        finally:
            os.remove(image_path)

        output = BytesIO()
        output.write(pdf.output(dest="S"))
        output.seek(0)
        return output

    pdf_bytes = generate_pdf()
    st.download_button("📄 Download Report as PDF", data=pdf_bytes, file_name="tree_comparison.pdf", mime="application/pdf")

except FileNotFoundError:
    st.error("Error: 'strict_filtered_species_data.csv' not found. Please ensure the CSV file is in the same directory.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}. Please check your code and data.")
