import streamlit as st
import pandas as pd
import requests, json


#WoS API headers
headers = {'X-ApiKey': st.secrets['API_KEY'], 
           'Accept': 'application/json'}

#WoS API query 
baseUrl = 'https://api.clarivate.com/apis/wos-starter/v1/documents?q=(DO='

#read in most recent JIF data
IFs = pd.read_csv(r"https://raw.githubusercontent.com/martindalete/JIF_Tool/main/JIFs.csv?raw=true")
#create empty lists to which we will append API-gathered data
ISSN_data = []
eISSN_data = []
csv = None

@st.cache(suppress_st_warning=True)
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

@st.cache(suppress_st_warning=True)
def api_loop(dataframe):
    global csv
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        DOI = str(df.iloc[i]['DOIs'])
        queryUrl = baseUrl + DOI + ')'  
        r = requests.get(queryUrl, headers=headers)
        rText = r.text
        results = json.loads(rText) 
        try:
            issn = results['hits'][0]['identifiers']['issn']
        except:
            issn = 'NA'
        try:
            eISSN = results['hits'][0]['identifiers']['eissn']
        except:
            eISSN = 'NA'
        ISSN_data.append([DOI,issn])
        eISSN_data.append([DOI,eISSN])
        my_bar.progress(percent_complete)

    #assign ISSN/eISSN lists to dataframes
    ISSN_df = pd.DataFrame(ISSN_data, columns = ['DOI','ISSN'])
    eISSN_df = pd.DataFrame(eISSN_data, columns = ['DOI','eISSN'])
    
    #merge (join) found data with JIF data
    ISSN_left_merged = pd.merge(ISSN_df, IFs, how = "left", on=['ISSN', 'ISSN'])
    eISSN_left_merged = pd.merge(eISSN_df, IFs, how = "left", on=['eISSN', 'eISSN'])
    
    #subset merged data to only show columns for DOI and JIF
    ISSN_abbreviated = ISSN_left_merged[['DOI','Journal Impact Factor']]
    eISSN_abbreviated = eISSN_left_merged[['DOI','Journal Impact Factor']]
    
    #stack ISSN/eISSN dataframes on top of each other and then...
    df_final = pd.concat([ISSN_abbreviated, eISSN_abbreviated])
    df_final = df_final.reset_index(drop=True)
    
    #drop rows where JIF is empty
    df_final = df_final[df_final['Journal Impact Factor'].notna()]
    #deduplicate rows 
    df_final = df_final.drop_duplicates()
    
    #display final dataframe
    st.dataframe(df_final)
    
    csv = convert_df(df_final)

@st.cache(suppress_st_warning=True)
def show_download_button():
    global csv
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='DOIs_with_JIFs.csv',
        mime='text/csv')

#streamlit upload button
data = st.file_uploader("Upload a CSV of DOIs, one per line, no header column")

#read in uploaded CSV and write to dataframe
if data is not None:
    df = pd.read_csv(data, header=None)
    df = df.rename(columns={0: 'DOIs'})
    #display dataframe of uploaded DOIs     
    st.write(df)
    #introduce streamlit proress bar widget
    my_bar = st.progress(0.0)
    api_loop(df)
    if csv is not None:
        show_download_button()
