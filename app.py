import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from PIL import Image

# Load dataset
df = pd.read_csv("species_data.csv")
df.columns = df.columns.str.strip()

# Streamlit UI
st.title("🌳 Tree CO₂ Sequestration Estimator")

species = st.selectbox("Choose a Tree Species", df["common_name"])
years = st.slider("Select Time Period (years)", 1, 50, 20)
num_trees = st.number_input("Enter Number of Trees", min_value=1, value=100)

# Get species data
tree_data = df[df["common_name"] == species].iloc[0]
growth_rate = tree_data["Avg. DBH Growth (cm/year)"]
carbon_fraction = tree_data["Carbon Fraction"]
survival_rate = tree_data["Survival Rate"]

# Sequestration model
def calculate_co2(growth, carbon_frac, survival, year, trees):
    avg_dbh = growth * year
    biomass_kg = 0.25 * (avg_dbh ** 2) * year
    carbon_kg = biomass_kg * carbon_frac
    co2_kg = carbon_kg * 3.67
    total_co2 = co2_kg * trees * survival
    return total_co2 / 1000  # metric tons

total_co2_tons = calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees)

st.success(f"🌱 Estimated CO₂ Sequestration: {total_co2_tons:.2f} metric tons over {years} years.")

# Generate graph: CO₂ vs Years
def create_graph():
    x_vals = list(range(1, years + 1))
    y_vals = [calculate_co2(growth_rate, carbon_fraction, survival_rate, y, num_trees) for y in x_vals]

    fig, ax = plt.subplots()
    ax.plot(x_vals, y_vals, marker='o', color='green')
    ax.set_title(f"CO₂ Sequestered over {years} Years\n({species}, {num_trees} Trees)")
    ax.set_xlabel("Years")
    ax.set_ylabel("CO₂ Sequestered (metric tons)")
    ax.grid(True)

    img_buf = BytesIO()
    fig.savefig(img_buf, format='PNG')
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

graph_img = create_graph()
st.subheader("📈 CO₂ Sequestered Over Time")
st.image(graph_img, use_column_width=True)

# Generate PDF report with embedded graph
def generate_pdf_with_graph(image_buf):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Tree CO₂ Sequestration Report", ln=True, align='C')
    pdf.ln(10)

    # Info
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Species: {species}", ln=True)
    pdf.cell(200, 10, f"Years: {years}", ln=True)
    pdf.cell(200, 10, f"Number of Trees: {int(num_trees)}", ln=True)
    pdf.cell(200, 10, f"Estimated CO₂ Sequestered: {total_co2_tons:.2f} metric tons", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, "Model Details:", ln=True)
    pdf.cell(200, 10, f"- Avg. DBH Growth: {growth_rate} cm/year", ln=True)
    pdf.cell(200, 10, f"- Carbon Fraction: {carbon_fraction}", ln=True)
    pdf.cell(200, 10, f"- Survival Rate: {survival_rate}", ln=True)

    # Save image to temp PNG file
    image = Image.open(image_buf)
    temp_image_path = "/tmp/temp_graph.png"
    image.save(temp_image_path)

    # Add graph image to PDF
    pdf.image(temp_image_path, x=10, y=None, w=180)

    # Return as BytesIO
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

pdf_file = generate_pdf_with_graph(graph_img)

# Download button
st.download_button(
    label="📄 Download Report as PDF",
    data=pdf_file,
    file_name=f"{species.replace(' ', '_')}_CO2_Report.pdf",
    mime="application/pdf"
)
