import streamlit as st
import pandas as pd
import requests, json
import time
st.experimental_memo.clear()
st.set_page_config(page_title="JIFs from DOIs")
st.title("JIFS from DOIs")
#Scopus API headers
headers = {'X-ELS-APIKey': st.secrets['API_KEY'], 
           'Accept': 'application/json'}
#Scopus API query 
url = 'https://api.elsevier.com/content/abstract/doi/'
#read in most recent JIF data
IFs = pd.read_csv(r"https://raw.githubusercontent.com/martindalete/JIF_Tool/main/JIFs_2022-08-26.csv?raw=true")
IFs['ISSN'] = IFs['ISSN'].str.replace('-', '')
IFs['eISSN'] = IFs['eISSN'].str.replace('-', '')
#create empty lists to which we will append API-gathered data
identifiers = []
csv = None
#convert dataframe to csv for exporting purposes
@st.experimental_memo(suppress_st_warning=True)
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')
#main function that uses list of DOIs with API call
@st.experimental_memo(suppress_st_warning=True)
def api_loop(dataframe):
    global csv
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        DOI = str(df.iloc[i]['DOIs'])
        queryURL = url + DOI
        r = requests.get(queryURL, headers=headers)
        rText = r.text
        rJSON = json.loads(rText)
        try:
            ids = rJSON['abstracts-retrieval-response']['coredata']['prism:issn']
        except:
            ids = 'No ISSN(s) Found'
        try:
            eISSN = ids.split(' ')[0]
        except:
            eISSN = 'No eISSN Found'
        try:
            ISSN = ids.split(' ')[1]
        except:
            ISSN = 'No ISSn Found'
        try:
            title = rJSON['abstracts-retrieval-response']['coredata']['prism:publicationName']
        except:
            title = 'No Title Found'
        try:
            times_cited = rJSON['abstracts-retrieval-response']['coredata']['citedby-count']
        except:
            times_cited = 'No Citations Found'
        identifiers.append([DOI,ISSN,title,times_cited])
        identifiers.append([DOI,eISSN,title,times_cited])
        my_bar.progress(percent_complete)
        time.sleep(0.05)
    identifiers_df = pd.DataFrame(identifiers, columns = ['DOI','Identifier','Journal Title','Times Cited'])
    
    #merge (join) found data with JIF data
    identifiers_merged_1 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['eISSN'])
    identifiers_merged_2 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['ISSN'])
    
    #subset merged data to only show columns for DOI and JIF
    identifiers_abbreviated_1 = identifiers_merged_1[['DOI','Journal Impact Factor', 'Journal Title', 'Times Cited']]
    identifiers_abbreviated_2 = identifiers_merged_2[['DOI','Journal Impact Factor', 'Journal Title', 'Times Cited']]
    
    #stack ISSN/eISSN dataframes on top of each other and then...
    df_final_2 = pd.concat([identifiers_abbreviated_1, identifiers_abbreviated_2])
    
    df_final_2 = df_final_2.reset_index(drop=True)
    
    #display final dataframe
    df_final_2 = df_final_2.drop_duplicates()
    test_df = df_final_2.sort_values('Journal Impact Factor', ascending=False)
    test_df = test_df[~test_df.duplicated('DOI')]
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].astype(str)
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].replace('nan', 'No JIF Found')
    test_df = test_df.reset_index(drop=True)
    st.dataframe(test_df)
    
    #convert df to csv
    csv = convert_df(test_df)
@st.experimental_memo(suppress_st_warning=True)
def show_download_button():
    global csv
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='DOIs_with_JIFs.csv',
        mime='text/csv')
        
#streamlit upload button
data = st.file_uploader("Upload a CSV of DOIs, one per line, no header column",
                       key = '1',
                       help='Make sure your upload file is a CSV and only contains DOIs, one per line, with no header')
#read in uploaded CSV and write to dataframe
if data is not None:
    df = pd.read_csv(data, header=None)
    df = df.rename(columns={0: 'DOIs'})
    #display dataframe of uploaded DOIs     
    st.dataframe(df)
    #introduce streamlit proress bar widget
    my_bar = st.progress(0.0)
    api_loop(df)
    if csv is not None:
        st.balloons()              
        st.success('Your Download is Ready!')
        show_download_button()
