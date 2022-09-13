import pandas as pd
import streamlit as st
import requests
import json
import base64

st.experimental_memo.clear()
st.set_page_config(page_title="JIFs from RES")
st.title("JIFS from RES")

headers = {'Mailto':'martindalete@ornl.gov'}

identifiers = []
data = None
csv = None

counter = 0

IFs = pd.read_csv(r"https://raw.githubusercontent.com/martindalete/JIF_Tool/main/JIFs_2022-08-26.csv?raw=true")

#convert dataframe to csv for exporting purposes
@st.experimental_memo(suppress_st_warning=True)
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

#main function that uses list of DOIs with API call
@st.experimental_memo(suppress_st_warning=True)
def crossref_loop(dataframe):
    global csv
    global counter
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        try:
            DOI = str(df.iloc[i]['DOI'].replace(' ',''))
        except:
            DOI = ''
            pub_id = df.iloc[i]['Pub Id']
            ids = 'No ISSN(s) Found'
            ISSN = 'No ISSN Found'
            eISSN = 'No ISSN Found'
            article_title = 'No Article Title Found'
            times_cited = 0
            source_title = 'No Source Title Found'
            identifiers.append([counter,pub_id,DOI,ISSN,source_title,article_title,times_cited])
            identifiers.append([counter,pub_id,DOI,eISSN,source_title,article_title,times_cited])
            counter += 1
            my_bar.progress(percent_complete)
            continue
        try:
            pub_id = df.iloc[i]['Pub Id']
        except:
            pub_id = 'No Pub Id Found'
        r = requests.get('https://api.crossref.org/works/'+DOI+'?mailto=martindalete@ornl.gov')        
        rText = r.text
        try:
            crossref_payload = json.loads(rText)        
        except:
            ids = 'No ISSN(s) Found'
            ISSN = 'No ISSN Found'
            eISSN = 'No ISSN Found'
            article_title = 'No Article Title Found'
            times_cited = 0
            source_title = 'No Source Title Found'
            identifiers.append([counter,pub_id,DOI,ISSN,source_title,article_title,times_cited])
            identifiers.append([counter,pub_id,DOI,eISSN,source_title,article_title,times_cited])
            counter += 1
            my_bar.progress(percent_complete)
            continue
        try:
            ids = crossref_payload['message']['ISSN']
        except:
            ids = 'No ISSN(s) Found'
            ISSN = 'No ISSN Found'
            eISSN = 'No ISSN Found'
            try:
                article_title = crossref_payload['title'][0]
            except:
                article_title = 'No Article Title Found'
            try:
                source_title = crossref_payload['message']['container-title'][0]
            except:
                source_title = 'No Source Title Found'
            try:
                times_cited = crossref_payload['message']['is-referenced-by-count']
            except:
                times_cited = 0
            identifiers.append([counter,pub_id,DOI,ISSN,source_title,article_title,times_cited])
            identifiers.append([counter,pub_id,DOI,eISSN,source_title,article_title,times_cited])
            counter += 1
            my_bar.progress(percent_complete)
            continue
        try:
            ISSN = ids[0]
        except:
            ISSN = 'No ISSN Found'
        try:
            eISSN = ids[1]
        except:
            eISSN = 'No ISSN Found'
        try:
            article_title = crossref_payload['message']['title'][0]
        except:
            article_title = 'No Title Found'
        try:
            source_title = crossref_payload['message']['container-title'][0]
        except:
            source_title = 'No Source Title Found'        
        try:
            times_cited = crossref_payload['message']['is-referenced-by-count']
        except:
            times_cited = 0
        identifiers.append([counter,pub_id,DOI,ISSN,source_title,article_title,times_cited])
        identifiers.append([counter,pub_id,DOI,eISSN,source_title,article_title,times_cited])
        my_bar.progress(percent_complete)
        counter += 1

    identifiers_df = pd.DataFrame(identifiers, columns = ['Index','Pub Id','DOI','Identifier','Source Title','Article Title','Times Cited'])

    #merge (join) found data with JIF data
    identifiers_merged_1 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['eISSN'])
    identifiers_merged_2 = pd.merge(identifiers_df, IFs, how = "left", left_on=['Identifier'], right_on=['ISSN'])

    #subset merged data to only show columns for DOI and JIF
    identifiers_abbreviated_1 = identifiers_merged_1[['Index','Pub Id', 'DOI','Identifier','Journal Impact Factor', 'Source Title', 'Article Title', 'Times Cited']]
    identifiers_abbreviated_2 = identifiers_merged_2[['Index','Pub Id', 'DOI','Identifier','Journal Impact Factor', 'Source Title', 'Article Title', 'Times Cited']]

    #stack ISSN/eISSN dataframes on top of each other and then...
    df_final_2 = pd.concat([identifiers_abbreviated_1, identifiers_abbreviated_2])
    df_final_2 = df_final_2.reset_index(drop=True)

    #display final dataframe
    df_final_2 = df_final_2.drop_duplicates()
    test_df = df_final_2.sort_values('Journal Impact Factor', ascending=False)
    test_df = test_df.drop_duplicates(['Pub Id'])
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].astype(str)
    test_df['Journal Impact Factor'] = test_df['Journal Impact Factor'].replace('nan', 'No JIF Found')
    test_df = test_df.reset_index(drop=True)
    test_df = test_df.sort_values('Index', ascending=True)
    test_df = test_df.drop('Index', axis=1)
    spam = test_df[pd.to_numeric(test_df['Journal Impact Factor'], errors='coerce').notnull()]
    count_all_pubs = str(len(test_df))
    count_jif_pubs = str(len(spam))
    percent_jif_pubs = str(round((len(spam)/len(test_df))*100))
    avg_jif = str(round(spam['Journal Impact Factor'].astype(float).mean(),2))
    median_jif = str(spam['Journal Impact Factor'].astype(float).median())
    jifs_over_5 = str(spam[spam['Journal Impact Factor'].astype(float) > 5].shape[0])
    percent_over_5 = str(round(((spam[spam['Journal Impact Factor'].astype(float) > 5].shape[0])/float(count_jif_pubs))*100))
    jifs_over_10 = str(spam[spam['Journal Impact Factor'].astype(float) > 10].shape[0])
    percent_over_10 = str(round(((spam[spam['Journal Impact Factor'].astype(float) > 10].shape[0])/float(count_jif_pubs))*100))
    st.write('Total Number of RES Pubs Submitted: ' + count_all_pubs)
    st.write('Total Number of RES Pubs with JIF: ' + count_jif_pubs)
    st.write('Percentage of RES Pubs with JIF: ' + percent_jif_pubs + '%')
    st.write('Average JIF for RES Pubs with JIF: ' + avg_jif)
    st.write('Median JIF for RES Pubs with JIF: ' + median_jif)
    st.write('Number of JIFs > 5: ' + jifs_over_5)
    st.write('Percentage of RES Pubs with JIF > 5: ' + percent_over_5 + '%')
    st.write('Number of JIFs > 10: ' + jifs_over_10)
    st.write('Percentage of RES Pubs with JIF > 10: ' + percent_over_10 + '%')    
    st.dataframe(test_df)
    st.markdown(get_table_download_link(test_df), unsafe_allow_html=True)

    
@st.experimental_memo(suppress_st_warning=True)
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'
    
with st.form("my-form", clear_on_submit=True):
    data = st.file_uploader('Upload data data.  Make sure you have columns with at least DOIs and Pub IDs, with headers that read "DOI" and "Pub Id".  The standard RES output format is acceptable',
                       key = '1',
                       help='This widget accepts both CSV and XLSX files. The standard RES output format is acceptable.')
    submitted = st.form_submit_button("Start the Process")

    if submitted and data is not None:
        st.write("Your Data:")
        if data.name.lower().endswith('.csv'):
            df = pd.read_csv(data, header=[0])
            #display dataframe of uploaded DOIs     
            st.dataframe(df)
            #introduce streamlit proress bar widget
            my_bar = st.progress(0.0)
            crossref_loop(df)
            st.balloons()              
            st.success('Your Download is Ready!')

        elif data.name.lower().endswith('.xlsx'):
            df = pd.read_excel(data, header=[0])
            #display dataframe of uploaded DOIs     
            st.dataframe(df)
            #introduce streamlit proress bar widget
            my_bar = st.progress(0.0)
            crossref_loop(df)
            st.balloons()              
            st.success('Your Download is Ready!')
