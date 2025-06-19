import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os

# Load dataset
df = pd.read_csv("filtered_india_tree_data.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# 🔒 Fixed: 30 Indian cities only
indian_cities = [
    "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Nashik", "Faridabad",
    "Meerut", "Rajkot", "Kalyan", "Vasai", "Varanasi", "Srinagar", "Ranchi", "Amritsar", "Jodhpur", "Coimbatore"
]

# 🔒 Fixed: 70 Indian tree species only
indian_tree_species = [
    "Neem", "Peepal", "Banyan", "Ashoka", "Gulmohar", "Teak", "Sal", "Sandalwood", "Arjun", "Jamun",
    "Amla", "Mango", "Jackfruit", "Tamarind", "Eucalyptus", "Mahogany", "Kachnar", "Kadamba", "Palash", "Semal",
    "Khejri", "Champa", "Bael", "Bakul", "Ber", "Imli", "Babool", "Subabul", "Custard Apple", "Drumstick",
    "Indian Cork", "Indian Laburnum", "Shirish", "Rudraksha", "Harsingar", "Kari Patta", "Beheda", "Bel", "Pongamia", "Flame of the Forest",
    "Raintree", "Silver Oak", "Bottlebrush", "Casuarina", "Indian Gooseberry", "Guava", "Fig", "Indian Almond", "Indian Coral Tree", "Papaya",
    "Sapodilla", "Mulberry", "Litchi", "Avocado", "Alstonia", "Chikoo", "Putranjiva", "Chinaberry", "Rosewood", "Cassia",
    "Kanchan", "Devil Tree", "Tendu", "Siris", "Chandan", "Shisham", "Pipal", "Mast Tree", "Indian Beech", "Gmelina"
]

# User input: city and species (predefined lists)
st.title("🌳 Tree CO2 Sequestration Comparator (India)")

city = st.selectbox("Select Your City (India Only)", sorted(indian_cities))
species = st.selectbox("Choose a Tree Species (India Only)", sorted(indian_tree_species))
nickname = st.text_input("Give a Nickname to Your Tree", "My Tree")
years = st.slider("Years to Estimate CO₂", 1, 50, 20)
num_trees = st.number_input("Number of Trees", min_value=1, value=10)

# Filter the dataset for valid species only
df = df[df["common_name"].isin(indian_tree_species)]

# Get species data
tree_data = df[df["common_name"].str.lower() == species.lower()]
if tree_data.empty:
    st.error("This tree species is not available in the dataset.")
    st.stop()
tree_data = tree_data.iloc[0]

# CO2 calculation logic
def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees):
    dbh = growth_rate * years
    biomass = 0.25 * (dbh ** 2) * years
    carbon = biomass * carbon_fraction
    co2 = carbon * 3.67
    return (co2 * survival_rate * num_trees) / 1000  # metric tons

user_co2 = calculate_co2(tree_data["avg_dbh_growth"], tree_data["carbon_fraction"], tree_data["survival_rate"], years, num_trees)
st.success(f"Estimated CO2 for {species}: {user_co2:.2f} metric tons")

# AI suggestion (better tree only)
ai_df = df[df["common_name"].str.lower() != species.lower()]
ai_df["estimated_co2"] = ai_df.apply(lambda row: calculate_co2(
    row["avg_dbh_growth"], row["carbon_fraction"], row["survival_rate"], years, num_trees), axis=1)
ai_df = ai_df[ai_df["estimated_co2"] > user_co2]

if not ai_df.empty:
    ai_best = ai_df.sort_values("estimated_co2", ascending=False).iloc[0]
    ai_species = ai_best["common_name"]
    ai_co2 = ai_best["estimated_co2"]
    st.info(f"AI Suggests: {ai_species}")
    st.success(f"Estimated CO2: {ai_co2:.2f} metric tons")
else:
    ai_species = None
    ai_co2 = 0
    st.warning("No better tree found by AI for your selection.")

# CO2 Comparison Chart
def generate_chart(user_co2, ai_co2):
    fig, ax = plt.subplots()
    ax.bar(["Your Tree", "AI Tree"], [user_co2, ai_co2], color=["green", "blue"])
    ax.set_ylabel("CO2 Sequestered (metric tons)")
    ax.set_title("User vs AI Tree Comparison")
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

chart_img = generate_chart(user_co2, ai_co2)
st.image(chart_img, caption="User vs AI Tree CO2", use_container_width=True)

# PDF generator
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Tree CO2 Comparison Report", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"City: {city}", ln=True)
    pdf.cell(190, 10, f"Tree Chosen: {species} (Nickname: {nickname})", ln=True)
    pdf.cell(190, 10, f"Estimated CO2: {user_co2:.2f} metric tons", ln=True)
    if ai_species:
        pdf.cell(190, 10, f"AI Suggested Tree: {ai_species}", ln=True)
        pdf.cell(190, 10, f"Estimated CO2: {ai_co2:.2f} metric tons", ln=True)
    else:
        pdf.cell(190, 10, "No better tree suggested by AI.", ln=True)
    image_path = "/tmp/co2_chart.png"
    with open(image_path, "wb") as f:
        f.write(chart_img.getbuffer())
    pdf.image(image_path, x=10, w=180)
    os.remove(image_path)
    output = BytesIO()
    output.write(pdf.output(dest="S").encode('latin1'))
    output.seek(0)
    return output

# PDF Download
pdf_bytes = generate_pdf()
st.download_button("📄 Download CO2 Comparison Report", data=pdf_bytes, file_name="tree_comparison.pdf", mime="application/pdf")
