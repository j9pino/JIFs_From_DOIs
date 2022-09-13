import streamlit as st
import pandas as pd
import requests, json
import time
import base64

st.experimental_memo.clear()
st.set_page_config(page_title="FY Converter")
st.title("Pubs: Convert Calendar Year to Fiscal Year")

headers = {'Mailto':'martindalete@ornl.gov'}

#create empty lists to which we will append API-gathered data
results_list = []
  
#convert dataframe to csv for exporting purposes
@st.experimental_memo(suppress_st_warning=True)
def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

#main function that uses list of DOIs with API call
@st.experimental_memo(suppress_st_warning=True)
def api_loop(dataframe):
    global dates_df
    for i in range(len(df)):
        percent_complete = (i+1)/len(df)
        try:
            DOI = str(df.iloc[i]['DOI'].replace(' ',''))
        except:
            DOI = ''
            title = ''
            pub_date = ''
            FY = ''
            results_list.append([DOI,title,pub_date,FY])
            my_bar.progress(percent_complete)
            continue
        r = requests.get('https://api.crossref.org/works/'+DOI+'?mailto=martindalete@ornl.gov')        
        rText = r.text
        rJSON = json.loads(rText)
        try:
            title = rJSON['message']['title'][0]
        except:
            title = 'No Article Title Found'
        try:
            try:
                year = rJSON['message']['published']['date-parts'][0][0]
            except:
                year = 'XXXX'
            try:
                month = rJSON['message']['published']['date-parts'][0][1]
            except:
                month = 'XX'
            try:
                day = rJSON['message']['published']['date-parts'][0][2]
            except:
                day = 'XX'
            pub_date = str(year)+'-'+ \
                        str(month)+'-'+ \
                        str(day)
        except:
            pub_date = ''
        try:
            if month == 'XX':
                FY = 'NA'
            elif int(month) >= 10:
                FY = int(year)+1
            else:
                FY = year
        except:
            FY = 'No published date found'
        results_list.append([DOI,title,pub_date,FY])
        my_bar.progress(percent_complete)
        time.sleep(0.05)
    dates_df = pd.DataFrame(results_list, columns = ['DOI','title','pub_date', 'FY'])
    
    dates_df = dates_df.reset_index(drop=True)
    dates_df['FY'] = dates_df['FY'].astype(str)
    dates_df['pub_date'] = dates_df['pub_date'].astype(str)
    
    #display final dataframe
    dates_df = dates_df.drop_duplicates()
    st.dataframe(dates_df)
    st.markdown(get_table_download_link(dates_df), unsafe_allow_html=True)


@st.experimental_memo(suppress_st_warning=True)
def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Download csv file</a>'       

with st.form("my-form", clear_on_submit=True):
    data = st.file_uploader('Upload data.  Make sure you have a column labeled "DOI". The standard RES output format is acceptable',
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
            api_loop(df)
            st.balloons()              
            st.success('Your Download is Ready!')

        elif data.name.lower().endswith('.xlsx'):
            df = pd.read_excel(data, header=[0])
            #display dataframe of uploaded DOIs     
            st.dataframe(df)
            #introduce streamlit proress bar widget
            my_bar = st.progress(0.0)
            api_loop(df)
            st.balloons()              
            st.success('Your Download is Ready!')        
