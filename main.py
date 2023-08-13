import requests, json
import pandas as pd

# result_type options
BATCH_DOWNLOAD = 'batch_download'
SEARCH = 'search'
# groups
EXPERIMENTAL = 'experimental'
CONTROL = 'control'

def write_data_to_json_file(response, filename):
    # Write to file
    f = open(f'data/{filename}.json', 'w')
    f.write(json.dumps(response, indent=4))
    f.close()

    # Load JSON data from file
    # with open(f'data/{filename}.json') as json_file:
    #     data = json.load(json_file)

    # # Count the number of results
    # num_results = len(data['@graph'])

    # print(f"Number of results, {filename}: {num_results}")


def get_accession_numbers(filename):
    accession_numbers = []
    # Load JSON data from file
    with open(f'data/{filename}.json') as json_file:
        data = json.load(json_file)
        for item in data['@graph']:
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


def get_search_results(url, filename):
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers).json()
    write_data_to_json_file(response, filename)


def get_batch_download_text_file(api_url : str, filename : str):
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.text

        # write to file
        f = open(f'data/{filename}-batch.txt', 'w')
        f.write(data)
        f.close()
    else:
        print("API call failed")


def get_file_from_api(accessionNum: str):
    # Force return from the server in JSON format
    headers = {'accept': 'application/json'}
    
    # This URL locates the ENCODE biosample with accession number ENCBS000AAA
    # url = f'https://www.encodeproject.org/biosample/{accessionNum}/?frame=object'
    url = f'https://www.encodeproject.org/files/{accessionNum}/?frame=object'
    
    return requests.get(url, headers=headers).json()


def get_fastq_file_urls(filename):
    with open(f'data/{filename}.txt') as file:
        text_data = file.read()
        data_list = {}
        lines = text_data.split('\n')[1:-1]
        for line in lines:
            # Process each line and split into fields
            split_line = line.split('/')
            files_index = split_line.index('files')
            accession = split_line[files_index + 1]
            data_list[accession] = line
        return data_list


def match_exper_to_controls(df):
    exper_accessions = get_accession_numbers('exper-search-results')

    for exper_accession in exper_accessions:
        exper_urls = get_fastq_file_urls('experimental-batch')
        if exper_accession in exper_urls:
            exper_file = get_file_from_api(exper_accession)
            possible_controls = exper_file.get('possible_controls', [])

            data = []
            if len(possible_controls) > 0:
                for control in possible_controls:
                    control_urls = get_fastq_file_urls('control-batch')
                    control_accession = control.split('/')[2]

                    if control_accession in control_urls:
                        control_file_str = control_urls[control_accession]
                        data.append({'experimental_file': exper_urls[exper_accession], 'control_file': control_file_str})
                    else:
                        data.append({'experimental_file': exper_urls[exper_accession]})
            else:
                data.append({'experimental_file': exper_urls[exper_accession]})

            df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
            
        # for control_accession in exper_file.possible_controls:
        #     control = get_file(control_accession)

        #     base_url = 'https://www.encodeproject.org'
        #     url_control = f'{base_url}{control.href}'
        #     url_exper = f'{base_url}{exper_file.href}'

        #     print(f'~~~EXPER: {url_exper} & CONTROL: {url_control}')
            # add exper file and control file(s) to table

"""
TODO:
create a table with experimental files in first column and controls in second
download experimentals text file
download controls text file
run search for experimental files and get array of accessions
download each experimental file in array of accessions
loop through files to get possible_controls from each
for each possible_control add a row to the dataframe with the experimental fastq file and the control fastq file
if there are no possible controls, add the exper fastq file and leave the control column empty
STRETCH: deal with replicates
STRETCH: verify accuracy
"""
# build table
df = pd.DataFrame(columns=["experimental_file", "control_file"])

# get batch download of available files
batch_url_exper = build_url(BATCH_DOWNLOAD, EXPERIMENTAL)
get_batch_download_text_file(batch_url_exper, EXPERIMENTAL)

batch_url_controls = build_url(BATCH_DOWNLOAD, CONTROL)
get_batch_download_text_file(batch_url_controls, CONTROL)

# get json search results
search_url_exper = build_url(SEARCH, EXPERIMENTAL)
print(search_url_exper)
get_search_results(search_url_exper, 'exper-search-results')

search_url_controls = build_url(SEARCH, CONTROL)
print(search_url_controls)
get_search_results(search_url_controls, 'controls-search-results')

# match up each experimental sample to its control(s)
match_exper_to_controls(df)

print(df)
