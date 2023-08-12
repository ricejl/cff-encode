import requests, json

def write_data_to_file(response, filename):
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


def get_search_result():
    headers = {'accept': 'application/json'}

    TYPE = 'Experiment'
    BIOSAMPLE_ONTOLOGY_TERM_NAME = 'HCT116'
    ASSAY_TERM_NAME_CHIP = 'ChIP-seq'
    ASSAY_TERM_NAME_MC = 'Mint-ChIP-seq' # only post-2015
    DATE_RELEASED_START = '2009-01-01'
    DATE_RELEASED_END = '2015-12-31'
    IS_CONTROL_TYPE = '&control_type=*'
    NOT_CONTROL_TYPE = '&control_type!=*'
    LIMIT = 'all'

    # TODO: put urls in array and loop over to get data (make get calls and write to file)
    # url = 'https://www.encodeproject.org/search/?type=Experiment&biosample_ontology.term_name=HCT116&assay_title=Mint-ChIP-seq&assay_title=Control+Mint-ChIP-seq&assay_title=TF+ChIP-seq&assay_title=Control+ChIP-seq&assay_title=Histone+ChIP-seq'
    url = ('https://www.encodeproject.org/search/?type=' + TYPE +
           '&biosample_ontology.term_name=' + BIOSAMPLE_ONTOLOGY_TERM_NAME +
           '&assay_term_name=' + ASSAY_TERM_NAME_CHIP +
           '&assay_term_name=' + ASSAY_TERM_NAME_MC +
           '&advancedQuery=date_released:[' + DATE_RELEASED_START + '%20TO%20' + DATE_RELEASED_END + ']' +
           '&limit=' + LIMIT)
    
    url_for_controls = url + IS_CONTROL_TYPE
    url_for_experimentals = url + NOT_CONTROL_TYPE

    # TODO: do these automatically await?
    response = requests.get(url, headers=headers).json()
    controls_response = requests.get(url_for_controls, headers=headers).json()
    exper_response = requests.get(url_for_experimentals, headers=headers).json()

    write_data_to_file(response, 'all-results')
    write_data_to_file(controls_response, 'controls-results')
    write_data_to_file(exper_response, 'exper-results')


def get_file(accessionNum: str):

    # Force return from the server in JSON format
    headers = {'accept': 'application/json'}
    
    # This URL locates the ENCODE biosample with accession number ENCBS000AAA
    # url = f'https://www.encodeproject.org/biosample/{accessionNum}/?frame=object'
    url = f'https://www.encodeproject.org/files/{accessionNum}/?frame=object'

    
    # GET the object
    response = requests.get(url, headers=headers)

    # Extract the JSON response as a Python dictionary
    # biosample = response.json()
    file = response.json()

    # return file instead of writing each one
    return file
    # Print the Python object
    # print(json.dumps(biosample, indent=4))
    print(json.dumps(file, indent=4))

    # Write to file
    # f = open(f'data/{accessionNum}.json', 'w')
    f = open(f'data/{accessionNum}.json', 'w')
    # f.write(json.dumps(biosample, indent=4))
    f.write(json.dumps(file, indent=4))
    f.close()


def match_exper_to_controls():
    experimental_accession_numbers = get_accession_numbers('exper-results')

    for exper_accession in experimental_accession_numbers:

        exper_file = get_file(exper_accession)

        if hasattr(exper_file, 'possible_controls'):
            print(f'YES for {exper_accession}')
        else:
            print(f'no possible control listed for {exper_accession}')
        # for control_accession in exper_file.possible_controls:
        #     control = get_file(control_accession)

        #     base_url = 'https://www.encodeproject.org'
        #     url_control = f'{base_url}{control.href}'
        #     url_exper = f'{base_url}{exper_file.href}'

        #     print(f'~~~EXPER: {url_exper} & CONTROL: {url_control}')
            # add exper file and control file(s) to table


# get_file('ENCSR101FJM')

# get_search_result()

match_exper_to_controls()

