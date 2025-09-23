import pandas as pd
import streamlit as st
import requests
import json
import base64
import numpy as np

st.set_page_config(page_title="JIFs from RES")
st.title("JIFs from RES")

headers = {'Mailto': 'pinojc@ornl.gov'}

# Load JIF data from a local file in the working directory
IFs = pd.read_csv("Incites_Publishers_2025.csv")

# Clean up IFs columns for better matching
IFs['ISSN'] = IFs['ISSN'].astype(str).str.strip()
IFs['eISSN'] = IFs['eISSN'].astype(str).str.strip()
IFs['Name'] = IFs['Name'].astype(str).str.strip().str.lower()  # Clean and normalize Name column

# Function to get JIF and citation count
def get_jif_and_citations(DOI, IFs):
    try:
        # Retrieve CrossRef data
        r = requests.get(f'https://api.crossref.org/works/{DOI}?mailto=pinojc@ornl.gov')
        if r.status_code != 200:
            print(f"CrossRef API request failed for DOI: {DOI}, status code: {r.status_code}")
            return np.nan, 0

        crossref_payload = r.json()  # Parse JSON response
        ids = crossref_payload['message'].get('ISSN', ['No ISSN Found'])
        times_cited = crossref_payload['message'].get('is-referenced-by-count', 0)
        
        # Extract ISSN, eISSN, and journal name, clean them up
        ISSN = ids[0].strip() if len(ids) > 0 else 'No ISSN Found'
        eISSN = ids[1].strip() if len(ids) > 1 else 'No ISSN Found'
        journal_name = crossref_payload['message'].get('container-title', ['No Name Found'])[0].strip().lower()

        # Try to find JIF using ISSN or eISSN
        jif_row = IFs[(IFs['ISSN'] == ISSN) | (IFs['eISSN'] == eISSN)]

        # If no match by ISSN/eISSN, try matching by Name
        if jif_row.empty:
            print(f"No match by ISSN/eISSN for DOI: {DOI}. Trying to match by journal name: {journal_name}")
            jif_row = IFs[IFs['Name'] == journal_name]

        # Log the matching attempt
        if jif_row.empty:
            print(f"No JIF found for DOI: {DOI} with ISSN: {ISSN}, eISSN: {eISSN}, or Name: {journal_name}")
        else:
            print(f"JIF found for DOI: {DOI} with ISSN: {ISSN}, eISSN: {eISSN}, or Name: {journal_name}")

        jif = jif_row['Journal Impact Factor'].iloc[0] if not jif_row.empty else np.nan

        return jif, times_cited
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # Log any errors
        print(f"Error processing DOI {DOI}: {e}")
        return np.nan, 0

# Function to process data and calculate JIFs
def process_data(dataframe, IFs, progress_bar):
    jif_times_cited = []
    total = len(dataframe)

    # Normalize column names
    dataframe.columns = map(str.lower, dataframe.columns)

    # Check if DOI column exists
    doi_column = 'doi' if 'doi' in dataframe.columns else None
    if not doi_column:
        st.error("DOI column not found!")
        return dataframe

    for i, row in dataframe.iterrows():
        DOI = str(row.get(doi_column, '')).replace(' ', '')
        jif, times_cited = get_jif_and_citations(DOI, IFs)
        jif_times_cited.append([DOI, jif, times_cited])

        # Update progress bar
        progress_bar.progress((i + 1) / total)

    # Create DataFrame for JIF and citations
    jif_times_cited_df = pd.DataFrame(jif_times_cited, columns=[doi_column, 'Journal Impact Factor', 'Times Cited'])
    
    # Merge results with original dataframe
    merged_df = pd.merge(dataframe, jif_times_cited_df, on=doi_column, how='left')
    return merged_df

# Function to create a download link for the CSV
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'

def display_summary(dataframe):
    dataframe.columns = map(str.lower, dataframe.columns)
    doi_column = 'doi'
    jif_column = 'journal impact factor'

    if doi_column not in dataframe.columns or jif_column not in dataframe.columns:
        st.warning("Required columns for summary not found.")
        return

    total_rows = len(dataframe)

    # Exclude blank DOIs from duplicate count
    non_blank_dois = dataframe[doi_column].dropna().astype(str).str.strip()
    duplicate_doi_count = non_blank_dois[non_blank_dois.duplicated()].nunique()

    # Filter out rows with blank DOIs, then drop duplicates for summary
    filtered_df = dataframe[dataframe[doi_column].notna() & (dataframe[doi_column].astype(str).str.strip() != "")]
    unique_df = filtered_df.drop_duplicates(subset=[doi_column])
    total_pubs = len(unique_df)

    pubs_with_jif = unique_df[jif_column].notna().sum()
    avg_jif = unique_df[jif_column].mean()
    median_jif = unique_df[jif_column].median()
    jif_above_5 = unique_df[unique_df[jif_column] > 5][jif_column].count()
    jif_above_10 = unique_df[unique_df[jif_column] > 10][jif_column].count()

    pct_with_jif = (pubs_with_jif / total_pubs) * 100 if total_pubs else 0
    pct_above_5 = (jif_above_5 / total_pubs) * 100 if total_pubs else 0
    pct_above_10 = (jif_above_10 / total_pubs) * 100 if total_pubs else 0

    st.subheader("Summary of Results")

    st.markdown(f"""
**File overview**
- Rows in uploaded file: **{total_rows}**
- Unique DOIs analyzed: **{total_pubs}**
- ⚠️ *Note: Rows with the same DOI may differ in other fields (e.g. Pub Id, Journal Name, etc.).*

**JIF statistics**
- Publications with JIF: **{pubs_with_jif}** ({pct_with_jif:.2f}%)
- Average JIF: **{avg_jif:.2f}**
- Median JIF: **{median_jif:.2f}**
- JIFs > 5: **{jif_above_5}** ({pct_above_5:.2f}%)
- JIFs > 10: **{jif_above_10}** ({pct_above_10:.2f}%)
""")

# Main Streamlit form
with st.form("my-form", clear_on_submit=True):
    data = st.file_uploader('Upload your file in CSV or Excel format. Please make sure there is a column labeled "DOI" to help the API correctly identify each publication.', key='1')
    submitted = st.form_submit_button("Start the Process")

    if submitted and data is not None:
        if data.name.lower().endswith('.csv'):
            df = pd.read_csv(data)
        elif data.name.lower().endswith('.xlsx'):
            df = pd.read_excel(data)

        if 'Pub Id' not in df.columns:
            df['Pub Id'] = range(1, len(df) + 1)

        st.dataframe(df)

        my_bar = st.progress(0.0)
        updated_df = process_data(df, IFs, my_bar)

        # Display the processed data
        st.dataframe(updated_df)

        # Display the summary of the results
        display_summary(updated_df)

        # Display the download link
        st.markdown(get_table_download_link(updated_df), unsafe_allow_html=True)

        st.balloons()              
        st.success('Your Download is Ready!')
