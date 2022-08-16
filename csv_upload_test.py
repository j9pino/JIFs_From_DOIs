import streamlit as st
import pandas as pd
import requests, json


#Scopus API headers
headers = {'X-ELS-APIKey': st.secrets['API_KEY'], 
           'Accept': 'application/json'}
#Scopus API query 
url = 'https://api.elsevier.com/content/abstract/doi/'

#read in most recent JIF data
IFs = pd.read_csv(r"https://raw.githubusercontent.com/martindalete/JIF_Tool/main/JIFs.csv?raw=true")
IFs['ISSN'] = IFs['ISSN'].str.replace('-', '')
IFs['eISSN'] = IFs['eISSN'].str.replace('-', '')
#st.dataframe(IFs)
#create empty lists to which we will append API-gathered data
ISSN_data = []
eISSN_data = []
identifiers = []
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
        queryURL = url + DOI
        #st.write(queryURL)
        r = requests.get(queryURL, headers=headers)
        rText = r.text
        rJSON = json.loads(rText)
        #st.write(rJSON)
        #pprint.pprint(rJSON)
        try:
            ids = rJSON['abstracts-retrieval-response']['coredata']['prism:issn']
        except:
            ids = 'NA'
        try:
            eISSN = ids.split(' ')[0]
        except:
            eISSN = 'NA'
        try:
            ISSN = ids.split(' ')[1]
        except:
            ISSN = 'NA'
        try:
            title = rJSON['abstracts-retrieval-response']['coredata']['prism:publicationName']
        except:
            title = ''
        ISSN_data.append([DOI,ISSN,title])
        eISSN_data.append([DOI,eISSN,title])
        identifiers.append([DOI,ISSN,title])
        identifiers.append([DOI,eISSN,title])
        my_bar.progress(percent_complete)
    #st.write(ISSN_data)
    #st.write(eISSN_data)
    #assign ISSN/eISSN lists to dataframes
    #ISSN_df = pd.DataFrame(ISSN_data, columns = ['DOI','ISSN','Journal Title'])
    #eISSN_df = pd.DataFrame(eISSN_data, columns = ['DOI','eISSN','Journal Title'])
    identifiers_df = pd.DataFrame(identifiers, columns = ['DOI','Identifier','Journal Title'])
    #st.dataframe(ISSN_df)
    #st.dataframe(eISSN_df)
    #st.dataframe(identifiers_df)
    
    #merge (join) found data with JIF data
    #ISSN_left_merged = pd.merge(ISSN_df, IFs, how = "left", on=['ISSN', 'ISSN'])
    #eISSN_left_merged = pd.merge(eISSN_df, IFs, how = "left", on=['eISSN', 'eISSN'])
    identifiers_merged_1 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['eISSN'])
    identifiers_merged_2 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['ISSN'])
    
    #subset merged data to only show columns for DOI and JIF
    #ISSN_abbreviated = ISSN_left_merged[['DOI','Journal Impact Factor', 'Journal Title']]
    #eISSN_abbreviated = eISSN_left_merged[['DOI','Journal Impact Factor', 'Journal Title']]
    identifiers_abbreviated_1 = identifiers_merged_1[['DOI','Journal Impact Factor', 'Journal Title']]
    identifiers_abbreviated_2 = identifiers_merged_2[['DOI','Journal Impact Factor', 'Journal Title']]
    #st.dataframe(ISSN_abbreviated)
    #st.dataframe(eISSN_abbreviated)
    #st.dataframe(identifiers_abbreviated_2)
    #st.dataframe(identifiers_abbreviated_1)
    #stack ISSN/eISSN dataframes on top of each other and then...
    #df_final = pd.concat([ISSN_abbreviated, eISSN_abbreviated])
    df_final_2 = pd.concat([identifiers_abbreviated_1, identifiers_abbreviated_2])
    #df_final = df_final.reset_index(drop=True)
    df_final_2 = df_final_2.reset_index(drop=True)
    
    #drop rows where JIF is empty
    #df_final = df_final[df_final['Journal Impact Factor'].notna()]
    df_final_2 = df_final_2[df_final_2['Journal Impact Factor'].notna()]
    #deduplicate rows 
    #df_final = df_final.drop_duplicates()
    df_final_2 = df_final_2.drop_duplicates()
    df_final_2 = df_final_2.reset_index(drop=True)
    
    #display final dataframe
    #st.dataframe(df_final)
    st.dataframe(df_final_2)
    
    #csv = convert_df(df_final)
    csv = convert_df(df_final_2)

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
    st.dataframe(df)
    #introduce streamlit proress bar widget
    my_bar = st.progress(0.0)
    api_loop(df)
    if csv is not None:
        show_download_button()
