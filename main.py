import requests
import pandas as pd

# result_type options
BATCH_DOWNLOAD = 'batch_download'
SEARCH = 'search'
# groups
EXPERIMENTAL = 'experimental'
CONTROL = 'control'

def get_accession_numbers(experiment):
    accession_numbers = []
    for item in experiment:
        accession_numbers.append(item['accession'])
    return accession_numbers


def build_url(result_type : str, control_type : str):
    TYPE = 'Experiment'
    BIOSAMPLE_ONTOLOGY_TERM_NAME = 'HCT116'
    ASSAY_TERM_NAME_CHIP = 'ChIP-seq'
    ASSAY_TERM_NAME_MC = 'Mint-ChIP-seq' # only post-2015
    DATE_RELEASED_START = '2009-01-01'
    DATE_RELEASED_END = '2015-12-31'
    IS_CONTROL_TYPE = '&control_type=*'
    NOT_CONTROL_TYPE = '&control_type!=*'
    FILE_TYPE = '&files.file_type=fastq'
    LIMIT = 'all'

    url = (f'https://www.encodeproject.org/{result_type}/' +
           '?type=' + TYPE +
           '&biosample_ontology.term_name=' + BIOSAMPLE_ONTOLOGY_TERM_NAME +
           '&assay_term_name=' + ASSAY_TERM_NAME_CHIP +
           '&assay_term_name=' + ASSAY_TERM_NAME_MC +
           '&advancedQuery=date_released:[' + DATE_RELEASED_START + '%20TO%20' + DATE_RELEASED_END + ']' +
           '&files.file_type=' + FILE_TYPE +
           '&limit=' + LIMIT)
    
    if control_type == 'control':
        return url + IS_CONTROL_TYPE
    elif control_type == 'experimental':
        return url + NOT_CONTROL_TYPE
    return url


def get_fastq_download_url(experiment_accession : str):
    return f'https://www.encodeproject.org/batch_download/?files.file_type=fastq&type=Experiment&@id=%2Fexperiments%2{experiment_accession}%2F&files.output_category=raw+data'


def get_search_results(url):
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers).json()
    return response['@graph']


def get_file_from_api(accessionNum: str):
    headers = {'accept': 'application/json'}
    url = f'https://www.encodeproject.org/files/{accessionNum}/?frame=object'

    return requests.get(url, headers=headers).json()


def match_exper_to_controls(exper_search):
    exper_accessions = get_accession_numbers(exper_search)

    data = []
    for exper_accession in exper_accessions:
        exper_file_url = get_fastq_download_url(exper_accession)
        exper_file = get_file_from_api(exper_accession)
        possible_controls = exper_file.get('possible_controls', [])

        if len(possible_controls) > 0:
            for control in possible_controls:
                control_accession = control.split('/')[2]
                control_file_url = get_fastq_download_url(control_accession)

                data.append({'experimental_file': exper_file_url, 'control_file': control_file_url})
        else:
            data.append({'experimental_file': exper_file_url})

    return data
        


# build table
df = pd.DataFrame(columns=["experimental_file", "control_file"])

# get json search results
search_url_exper = build_url(SEARCH, EXPERIMENTAL)
exper_search_results = get_search_results(search_url_exper)

# match up each experimental sample to its control(s)
result = match_exper_to_controls(exper_search_results)

df = pd.concat([df, pd.DataFrame(result)], ignore_index=True)
    
print(df)
df.to_csv('matched-controls.csv', index=False)
