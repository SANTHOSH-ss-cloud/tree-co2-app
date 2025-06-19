# Install if needed: pip install kagglehub[pandas-datasets]
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os
import kagglehub
from kagglehub import KaggleDatasetAdapter

# Load dataset from KaggleHub (5M Trees)
tree_file_path = "cleaned_dataset.csv"  # <-- Update with the correct file name if needed
trees_df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "mexwell/5m-trees-dataset",
    tree_file_path,
)

# Load static species dataset locally (contains co2, growth, etc.)
species_df = pd.read_csv("species_data.csv")

# Clean column names
trees_df.columns = trees_df.columns.str.strip().str.lower().str.replace(" ", "_")
species_df.columns = species_df.columns.str.strip().str.lower().str.replace(" ", "_")

# UI
st.title("🌳 AI-Based Tree CO₂ Sequestration Comparator")

st.subheader("User Tree Selection")
city = st.selectbox("Select Your City", sorted(trees_df["city"].dropna().unique()))
user_tree_name = st.text_input("Custom Tree Nickname", placeholder="Eg: My Green Hero")
species_options = species_df["common_name"].tolist()
user_species = st.selectbox("Choose Your Tree Species", species_options)
years = st.slider("Select Years to Project", 1, 50, 20)
num_trees = st.number_input("Number of Trees", min_value=1, value=10)

# Helper: Get species data by common name
def get_species_data(common_name):
    return species_df[species_df["common_name"] == common_name].iloc[0]

# CO₂ Calculation
def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees):
    avg_dbh = growth_rate * years
    biomass_kg = 0.25 * (avg_dbh ** 2) * years
    carbon_kg = biomass_kg * carbon_fraction
    co2_kg = carbon_kg * 3.67
    return (co2_kg * num_trees * survival_rate) / 1000  # metric tons

# AI Suggestion
st.subheader("🤖 AI Suggested Tree Based on Your City")

# Get all trees in selected city
city_trees = trees_df[trees_df["city"] == city]
ai_species = None
if not city_trees.empty:
    # Choose most common scientific_name with highest avg DBH
    avg_dbh_by_species = city_trees.groupby("scientific_name")["diameter_breast_height_cm"].mean().sort_values(ascending=False)
    for sci_name in avg_dbh_by_species.index:
        match = species_df[species_df["scientific_name"] == sci_name]
        if not match.empty:
            ai_species = match.iloc[0]
            break

if ai_species is not None:
    st.info(f"AI Suggests: **{ai_species['common_name']}** ({ai_species['scientific_name']})")
else:
    st.warning("No AI suggestion available for this city. Showing user choice only.")

# Get user species data
user_data = get_species_data(user_species)
user_co2 = calculate_co2(user_data["avg_dbh_growth"], user_data["carbon_fraction"], user_data["survival_rate"], years, num_trees)

# If AI data available, calculate its CO₂
if ai_species is not None:
    ai_co2 = calculate_co2(ai_species["avg_dbh_growth"], ai_species["carbon_fraction"], ai_species["survival_rate"], years, num_trees)
else:
    ai_co2 = 0

# Display results
st.success(f"🌱 Estimated CO₂ Sequestration (User Tree): **{user_co2:.2f} metric tons**")

if ai_species is not None:
    st.success(f"🤖 AI Estimated CO₂ Sequestration: **{ai_co2:.2f} metric tons**")

# Bar Chart Comparison
def create_comparison_chart():
    fig, ax = plt.subplots()
    names = ["Your Tree", "AI Suggested Tree"]
    values = [user_co2, ai_co2]
    ax.bar(names, values, color=["forestgreen", "dodgerblue"])
    ax.set_ylabel("CO₂ Sequestered (metric tons)")
    ax.set_title("Comparison of CO₂ Sequestration")
    buf = BytesIO()
    fig.savefig(buf, format="PNG")
    buf.seek(0)
    plt.close(fig)
    return buf

compare_chart = create_comparison_chart()
st.image(compare_chart, caption="User vs AI Tree", use_container_width=True)

# PDF Report
def generate_pdf(user_data, user_co2, ai_species, ai_co2, chart_img):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Tree CO₂ Sequestration Comparison Report", ln=True, align='C')
    pdf.set_font("Arial", "", 12)

    pdf.ln(10)
    pdf.cell(190, 10, f"City: {city}", ln=True)
    pdf.cell(190, 10, f"User Tree: {user_species} (Custom Name: {user_tree_name})", ln=True)
    pdf.cell(190, 10, f"User CO₂ Estimate: {user_co2:.2f} metric tons", ln=True)

    if ai_species is not None:
        pdf.cell(190, 10, f"AI Suggested Tree: {ai_species['common_name']} ({ai_species['scientific_name']})", ln=True)
        pdf.cell(190, 10, f"AI CO₂ Estimate: {ai_co2:.2f} metric tons", ln=True)

    chart_path = "/tmp/compare_chart.png"
    with open(chart_path, "wb") as f:
        f.write(chart_img.getbuffer())
    pdf.image(chart_path, x=10, w=180)
    os.remove(chart_path)

    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

pdf_file = generate_pdf(user_data, user_co2, ai_species, ai_co2, compare_chart)

# Download Button
st.download_button(
    label="📄 Download Report as PDF",
    data=pdf_file,
    file_name=f"{user_species.replace(' ', '_')}_vs_AI_CO2_Report.pdf",
    mime="application/pdf"
)
