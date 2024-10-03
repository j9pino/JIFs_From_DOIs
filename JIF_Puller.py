import pandas as pd
import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="JIFs from RES")
st.title("JIFs from RES")

headers = {'Mailto':'pinojc@ornl.gov'}

IFs = pd.read_csv(r"https://raw.githubusercontent.com/j9pino/JIFs_From_DOIs/main/Incites_Publishers_2024.csv")

def get_jif_and_citations(DOI, IFs):
    try:
        r = requests.get(f'https://api.crossref.org/works/{DOI}?mailto=pinojc@ornl.gov')        
        crossref_payload = json.loads(r.text)
        ids = crossref_payload['message'].get('ISSN', ['No ISSN Found'])
        times_cited = crossref_payload['message'].get('is-referenced-by-count', 0)
        ISSN = ids[0] if len(ids) > 0 else 'No ISSN Found'
        eISSN = ids[1] if len(ids) > 1 else 'No ISSN Found'

        jif_row = IFs[(IFs['ISSN'] == ISSN) | (IFs['eISSN'] == eISSN)]
        jif = jif_row['Journal Impact Factor'].iloc[0] if not jif_row.empty else 'No JIF Found'

        return jif, times_cited
    except json.JSONDecodeError:
        return 'No JIF Found', 0

def process_data(dataframe, IFs, progress_bar):
    jif_times_cited = []
    total = len(dataframe)

    # Normalize column names
    dataframe.columns = map(str.lower, dataframe.columns)
    
    # Check if DOI or Doi exists
    doi_column = 'doi' if 'doi' in dataframe.columns else None
    if not doi_column:
        st.error("DOI column not found!")
        return dataframe  # Return the original dataframe if no DOI column exists

    for i, row in dataframe.iterrows():
        DOI = str(row.get(doi_column, '')).replace(' ', '')
        jif, times_cited = get_jif_and_citations(DOI, IFs)
        jif_times_cited.append([DOI, jif, times_cited])

        progress_bar.progress((i + 1) / total)

    # Create jif_times_cited_df with a lowercase 'doi' column
    jif_times_cited_df = pd.DataFrame(jif_times_cited, columns=[doi_column, 'Journal Impact Factor', 'Times Cited'])
    
    # Merge based on the lowercase 'doi' column
    merged_df = pd.merge(dataframe, jif_times_cited_df, on=doi_column, how='left')
    return merged_df

def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'

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

        st.dataframe(updated_df)
        st.markdown(get_table_download_link(updated_df), unsafe_allow_html=True)
        st.balloons()              
        st.success('Your Download is Ready!')
