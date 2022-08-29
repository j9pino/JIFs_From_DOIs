import crossref_commons.retrieval
import streamlit as st
import pandas as pd
from habanero import counts

CR_API_MAILTO = {"Mailto": "martindalete@ornl.gov"}

headers = {'Mailto':'martindalete@ornl.gov'}

#read in most recent JIF data
IFs = pd.read_csv(r"https://raw.githubusercontent.com/martindalete/JIF_Tool/main/JIFs_2022-08-26.csv?raw=true")
#IFs = pd.read_csv(r"C:\Users\9ex\OneDrive - Oak Ridge National Laboratory\streamlit\JIF\JIFs_2022-08-26.csv")
#IFs['ISSN'] = IFs['ISSN'].str.replace('-', '')
#IFs['eISSN'] = IFs['eISSN'].str.replace('-', '')

#st.write(IFs)

#create empty lists to which we will append API-gathered data
identifiers = []
csv = None

#convert dataframe to csv for exporting purposes
@st.cache(suppress_st_warning=True)
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

#main function that uses list of DOIs with API call
@st.cache(suppress_st_warning=True)
def crossref_loop(dataframe):
    global csv
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        DOI = str(df.iloc[i]['DOIs'])
        try:
            crossref_payload = crossref_commons.retrieval.get_publication_as_json(str(DOI))
        except:
            ids = 'No ISSN(s) Found'
            ISSN = 'No ISSN Found'
            eISSN = 'No eISSN Found'
            article_title = 'No Article Title Found'
            times_cited = 0
            source_title = 'No Source Title Found'
            identifiers.append([DOI,ISSN,source_title,article_title,times_cited])
            identifiers.append([DOI,eISSN,source_title,article_title,times_cited])
            my_bar.progress(percent_complete)
            continue
        try:
            ids = crossref_payload['ISSN']
            #st.write(ids)
        except:
            ids = 'No ISSN(s) Found'
            ISSN = 'No ISSN Found'
            eISSN = 'No eISSN Found'
            try:
                article_title = crossref_payload['title'][0]
            except:
                article_title = 'No Article Title Found'
            try:
                source_title = crossref_payload['container-title'][0]
            except:
                source_title = 'No Source Title Found'
            try:
                times_cited = counts.citation_count(doi = str(DOI))
            except:
                times_cited = 0
            identifiers.append([DOI,ISSN,source_title,article_title,times_cited])
            identifiers.append([DOI,eISSN,source_title,article_title,times_cited])
            my_bar.progress(percent_complete)
            continue
        try:
            ISSN = ids[0]
        except:
            ISSN = 'No ISSN Found'
        try:
            eISSN = ids[1]
        except:
            eISSN = 'No eISSN Found'
        try:
            article_title = crossref_payload['title'][0]
        except:
            article_title = 'No Title Found'
        try:
            source_title = crossref_payload['container-title'][0]
        except:
            source_title = 'No Source Title Found'        
        try:
            times_cited = counts.citation_count(doi = str(DOI))
        except:
            times_cited = 0
        identifiers.append([DOI,ISSN,source_title,article_title,times_cited])
        identifiers.append([DOI,eISSN,source_title,article_title,times_cited])
        my_bar.progress(percent_complete)
    identifiers_df = pd.DataFrame(identifiers, columns = ['DOI','Identifier','Source Title','Article Title','Times Cited'])
    
    #merge (join) found data with JIF data
    identifiers_merged_1 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['eISSN'])
    identifiers_merged_2 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['ISSN'])
    
    #subset merged data to only show columns for DOI and JIF
    identifiers_abbreviated_1 = identifiers_merged_1[['DOI','Identifier','Journal Impact Factor', 'Source Title', 'Article Title', 'Times Cited']]
    identifiers_abbreviated_2 = identifiers_merged_2[['DOI','Identifier','Journal Impact Factor', 'Source Title', 'Article Title', 'Times Cited']]
    
    #stack ISSN/eISSN dataframes on top of each other and then...
    df_final_2 = pd.concat([identifiers_abbreviated_1, identifiers_abbreviated_2])
    
    df_final_2 = df_final_2.reset_index(drop=True)
    #st.write(df_final_2)
    
    #display final dataframe
    df_final_2 = df_final_2.drop_duplicates()
    #test_df = df_final_2.sort_values('Journal Impact Factor', ascending=False)
    #test_df = test_df[~test_df.duplicated('DOI')]
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].astype(str)
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].replace('nan', 'No JIF Found')
    test_df = test_df.reset_index(drop=True)

    st.dataframe(test_df)
    
    #convert df to csv
    csv = convert_df(test_df)

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
    crossref_loop(df)
    if csv is not None:
        st.balloons()              
        st.success('Your Download is Ready!')
        show_download_button()
