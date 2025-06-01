import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# Load the species dataset
df = pd.read_csv("species_data.csv")
df.columns = df.columns.str.strip()


st.title("🌳 Tree CO₂ Sequestration Estimator")

species = st.selectbox("Choose a Tree Species", df["common_name"])
years = st.slider("Select Time Period (years)", 1, 50, 20)
num_trees = st.number_input("Enter Number of Trees", min_value=1, value=100)

tree_data = df[df["common_name"] == species].iloc[0]

# Constants and calculation
growth_rate = tree_data["Avg. DBH Growth (cm/year)"]
carbon_fraction = tree_data["Carbon Fraction"]
survival_rate = tree_data["Survival Rate"]

# Simple model: CO2 sequestered = biomass * carbon_fraction * survival_rate * 3.67 (C to CO2)
# Biomass is approximated from DBH growth
avg_dbh = growth_rate * years
biomass_kg_per_tree = 0.25 * (avg_dbh ** 2) * years  # Simplified biomass model
carbon_kg = biomass_kg_per_tree * carbon_fraction
co2_kg_per_tree = carbon_kg * 3.67
total_co2_kg = co2_kg_per_tree * num_trees * survival_rate
total_co2_tons = total_co2_kg / 1000

st.success(f"🌱 Estimated CO₂ Sequestration: {total_co2_tons:.2f} metric tons over {years} years.")

# PDF Report Generator
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Tree CO₂ Sequestration Report", ln=True, align='C')
    
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Species: {species}", ln=True)
    pdf.cell(200, 10, f"Years: {years}", ln=True)
    pdf.cell(200, 10, f"Number of Trees: {num_trees}", ln=True)
    pdf.cell(200, 10, f"Estimated CO₂ Sequestered: {total_co2_tons:.2f} metric tons", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Model Details:", ln=True)
    pdf.cell(200, 10, f"- Avg. DBH Growth: {growth_rate} cm/year", ln=True)
    pdf.cell(200, 10, f"- Carbon Fraction: {carbon_fraction}", ln=True)
    pdf.cell(200, 10, f"- Survival Rate: {survival_rate}", ln=True)

    # Export to BytesIO
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# Download Button
pdf_file = generate_pdf()
st.download_button(
    label="📄 Download Report as PDF",
    data=pdf_file,
    file_name=f"{species.replace(' ', '_')}_CO2_Report.pdf",
    mime="application/pdf"
)
