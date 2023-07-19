import numpy as np
import matplotlib.pyplot as plt
import ads
import re
from unidecode import unidecode

#List of UDP Astro faculty
faculty = [
    "Aravena, M",
    "Assef, R",
    "Cieza, L",
    "Jenkins, J",
    "Johnston, E",
    "Jofre, P",
    "Mazzucchelli, C",
    "Prieto, J",
    "Ricci, C",
    "Yang, B",
    "Zurlo, A"
]

#List of UDP Astro students
students = [
    'Batalla Falcon, G', 
    'Brito Silva, D', 
    'De Brito Silva, D', 
    'Gonzalez Ruilova, C',
    'Gupta, K',
    'Hueichapan, E',
    'Jegatheesan, K',
    'Lambert, T', 
    'Nogueira, P', 
    'Pena Rojas, P',
    'Pessi, T',
    'Posses, A', 
    'Solimano, M',
    'Vitali, S',
    'Zewdie, D', 
    'de Brito Silva, D'
]

#People that have incorrectly had the affiliation in a paper.
black_listed = [
    'Apostolovski, Y',
    'Avenhaus, H',
    'Baughman, J', 
    'Brodie, J',
    'Carbillet, M', 
    'Casassus, S', 
    'Chauvin, G', 
    'Desgrange, C', 
    'Gilmore, G', 
    'Honig, S',
    'Lopez, H',
    'Perez, S',
    'Phadke, K', 
    'Reuter, C',
]

#Function to search for all papers from UDP in ADS in a given year. Specifically, we search for papers in which at least one author has a UDP affiliation. 
def paper_search(year):
    q = ads.SearchQuery(aff="portales", year=year, fl=["author", "citation_count", "aff", "property", "doctype", "title", "pubdate"], max_pages=100)
    ql = list(q)
    return ql


#Names can be written in different manners. This function removes accents, hyphens and everything after the first letter of the first name, so the result is always "last name, first name initial". 
def proc_name(input_name):
    name = unidecode(input_name)
    name = re.sub("-"," ", name)
    name = re.sub("^(.*?\, .).*$",r"\1", name)
    return name


#Determine if the author is a valid author to consider, and separate the udp authors in a list. 
def find_udp_authors(paper):
    if hasattr(paper, 'udp_authors'):
        return
    paper.udp_authors = list()
    for k in range(len(paper.author)):
        name = proc_name(paper.author[k])
        if re.search("portales", paper.aff[k], flags=re.IGNORECASE):
            if name in faculty or (re.search("astro", paper.aff[k], flags=re.IGNORECASE) and name not in black_listed):
                paper.udp_authors.append(name)
    return


#Function to filter out papers that should not be counted. 
def filter_papers(papers):
    filtered_papers = list()
    for paper in papers:

        #Only process refereed articles.
        if 'REFEREED' in paper.property and paper.doctype=='article':
            pass
        else:
            continue

        #Check that at least one author has an affiliation to astro-something at UDP, or is in the faculty least with an affiliation to UDP. The latter is important because in the beginning people published with only the Facultad de Ingenieria y Ciencias affiliation, without mentioning Nucleo or IEA. 
        find_udp_authors(paper)
        
        #If any authors pass the test, count the paper. 
        if len(paper.udp_authors)>0:
            filtered_papers.append(paper)
    return filtered_papers


#Distribute publications between UDP authors.
def get_n_papers(filtered_ads_query_list, only_faculty=False):
    n_papers = dict()
    for paper in filtered_ads_query_list:

        #If not counting only faculty authors, then check if the first author is a student. In that case, the paper counts wholely for the student. 
        w = np.zeros(len(paper.udp_authors))
        if not only_faculty:
            if paper.udp_authors[0] in students:
                w[0] = 1.0
            else:
                w[:] = 1./len(paper.udp_authors)
        else:
            for k, name in enumerate(paper.udp_authors):
                if name in faculty:
                    w[k] = 1.0
            if w.sum()>0:
                w = w/w.sum()

        #Now, add them. 
        for k, name in enumerate(paper.udp_authors):
            if name in n_papers:
                n_papers[name] += w[k]
            else:
                n_papers[name] = w[k]
    return n_papers

#Get the median av for each year.
def faculty_stats(n_papers, years):

    median_papers = np.zeros(years.shape)
    av_papers = np.zeros(years.shape)
    for i, year in enumerate(years):
        aux = list()
        for name in faculty:
            if name in n_papers[year]:
                aux.append(n_papers[year][name])
        #If there is a faculty with no papers in the last year, it should be reflected here. 
        if year==years[-1]:
            for name in faculty:
                if name not in n_papers[year]:
                    aux.append(0)
        median_papers[i] = np.median(aux)
        av_papers[i] = np.average(aux)
    return median_papers, av_papers

#Plot the evolution of faculty papers counting for incentivos. 
def evo_plot(n_papers, median_papers, av_papers, years, weights):
    fig, ax = plt.subplots(1, figsize=(10,8))
    for name in faculty:
        x = np.zeros(years.shape)
        for k,year in enumerate(years):
            if name in n_papers[year]:
                x[k] = n_papers[year][name]
        ax.plot(years, x, '--o', label=name, alpha=0.5)
    ax.plot(years, median_papers, '-bo', label='Mediana')
    ax.plot(years, av_papers, '--bs', label='Promedio')
    ax.plot(years, median_papers/weights, 'bo', label='Mediana Corr.', fillstyle='none', linestyle='dotted')
    ax.plot(years, av_papers/weights, 'bs', label='Promedio Corr.', fillstyle='none', linestyle='dotted')
    ax.legend()
    plt.show()
    return