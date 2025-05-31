import streamlit as st
import pandas as pd

# Load species dataset
df = pd.read_csv("species_data.csv")

st.title("🌳 Tree CO₂ Sequestration Estimator")

# Select tree species
species = st.selectbox("Choose a Tree Species", df["common_name"])

# Filter data for selected species
species_data = df[df["common_name"] == species].iloc[0]

st.markdown(f"""
**Scientific Name:** *{species_data['scientific_name']}*  
**Average DBH Growth:** {species_data['avg_dbh_growth']} cm/year  
**Carbon Fraction:** {species_data['carbon_fraction']}  
**Survival Rate:** {species_data['survival_rate']}
""")

# User inputs
age = st.number_input("Enter the age of the tree (in years):", min_value=1, max_value=200, value=10)
current_dbh = species_data['avg_dbh_growth'] * age  # Approximate DBH

# Calculate biomass and CO2 sequestration
# Biomass (approx) = 0.25 * DBH^2 (in kg)
biomass_kg = 0.25 * (current_dbh ** 2)
carbon_kg = biomass_kg * species_data['carbon_fraction']
co2_kg = carbon_kg * 3.67  # Convert C to CO₂

# Adjust for survival rate
adjusted_co2 = co2_kg * species_data['survival_rate']

# Show results
st.subheader("🌱 Estimated CO₂ Sequestration")
st.write(f"**DBH (approx):** {current_dbh:.2f} cm")
st.write(f"**Estimated Biomass:** {biomass_kg:.2f} kg")
st.write(f"**Carbon Stored:** {carbon_kg:.2f} kg")
st.write(f"**CO₂ Sequestered:** {co2_kg:.2f} kg")
st.success(f"🎯 **Adjusted CO₂ (Survival Rate): {adjusted_co2:.2f} kg**")

st.caption("Based on simplified estimation using DBH and species characteristics.")
