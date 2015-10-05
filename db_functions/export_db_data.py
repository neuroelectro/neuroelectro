import csv
import re
from django.conf import settings
from django.db.models import Q
import numpy as np
from db_functions.compute_field_summaries import computeArticleNedmSummary
from neuroelectro import models as m
from db_functions.author_search import get_article_last_author
import pandas as pd

__author__ = 'stripathy'


def export_db_to_data_frame():
    """Returns a nicely formatted pandas data frame of the ephys data and metadata for each stored article"""

    ncms = m.NeuronConceptMap.objects.all()#.order_by('-history__latest__history_date') # gets human-validated neuron mappings
    ephys_props = m.EphysProp.objects.all().order_by('-ephyspropsummary__num_neurons')
    ephys_names = [e.name for e in ephys_props]
    #ncms = ncms.sort('-changed_on')
    dict_list = []
    for ncm in ncms:

    #     # check if any nedms have any experimental factors assoc with them
    #     efcms = ne_db.ExpFactConceptMap.objects.filter(neuronephysdatamap__in = nedms)
    #     for efcm in efcms:
    #         nedms = ne_db.NeuronEphysDataMap.objects.filter(neuron_concept_map = ncm, exp_fact_concept_map = ).distinct()

        nedms = m.NeuronEphysDataMap.objects.filter(neuron_concept_map = ncm).distinct()
        if nedms.count() == 0:
            continue
        temp_dict = dict()
        temp_metadata_list = []
        for nedm in nedms:
            e = nedm.ephys_concept_map.ephys_prop
            temp_dict[e.name] = nedm.val_norm
            #temp_metadata_list.append(nedm.get_metadata())

        temp_dict['NeuronName'] =  ncm.neuron.name
        temp_dict['NeuronLongName'] =  ncm.neuron_long_name
        article = ncm.get_article()
        #article_metadata = normalize_metadata(article)
        metadata_list = nedm.get_metadata()
        out_dict = dict()
        for metadata in metadata_list:
            if not metadata.cont_value:
                if metadata.name in out_dict:
                    out_dict[metadata.name] = '%s, %s' % (out_dict[metadata.name], metadata.value)
                else:
                    out_dict[metadata.name] = metadata.value
            else:
                out_dict[metadata.name] = metadata.cont_value.mean
        temp_dict2 = temp_dict.copy()
        temp_dict2.update(out_dict)
        temp_dict = temp_dict2
        temp_dict['Title'] = article.title
        temp_dict['Pmid'] = article.pmid
        temp_dict['PubYear'] = article.pub_year
        temp_dict['TableID'] = ncm.source.data_table_id
        #print temp_dict
        dict_list.append(temp_dict)

    base_names = ['Title', 'Pmid', 'PubYear', 'TableID', 'NeuronName', 'NeuronLongName']
    nom_vars = ['Species', 'Strain', 'ElectrodeType', 'PrepType', 'JxnPotential']
    cont_vars  = ['JxnOffset', 'RecTemp', 'AnimalAge', 'AnimalWeight', 'FlagSoln']

    for i in range(0, 1):
        cont_vars.extend(['external_%s_Mg' % i, 'external_%s_Ca' % i, 'external_%s_Na' % i, 'external_%s_Cl' % i, 'external_%s_K' % i, 'external_%s_pH' % i, 'external_%s_text' % i, 'internal_%s_Mg' % i, 'internal_%s_Ca' % i, 'internal_%s_Na' % i, 'internal_%s_Cl' % i, 'internal_%s_K' % i, 'internal_%s_pH' % i, 'internal_%s_text' % i])
        #cont_var_headers.extend(['External_%s_Mg' % i, 'External_%s_Ca' % i, 'External_%s_Na' % i, 'External_%s_Cl' % i, 'External_%s_K' % i, 'External_%s_pH' % i, 'External_%s_text' % i, 'Internal_%s_Mg' % i, 'Internal_%s_Ca' % i, 'Internal_%s_Na' % i, 'Internal_%s_Cl' % i, 'Internal_%s_K' % i, 'Internal_%s_pH' % i, 'Internal_%s_text' % i])

    col_names = base_names + nom_vars + cont_vars + ephys_names
    df = pd.DataFrame(dict_list, columns = col_names)
    df = df.sort(['PubYear', 'Pmid', 'NeuronName'], ascending=[False, True, True])

    return df


def getAllArticleNedmMetadataSummary(getAllMetadata = False):
    """The old function for exporting the DB to a csv file, added here for reference"""
# TODO: uncomment and remove unnecessary metadata
#     articles = m.Article.objects.filter(Q(datatable__datasource__neuronconceptmap__times_validated__gte = 1) |
#         Q(usersubmission__datasource__neuronconceptmap__times_validated__gte = 1)).distinct()
#     articles = articles.filter(articlefulltext__articlefulltextstat__metadata_human_assigned = True ).distinct()
    articles = m.Article.objects.all()

    nom_vars = ['Species', 'Strain', 'ElectrodeType', 'PrepType', 'JxnPotential']
    cont_vars  = ['JxnOffset', 'RecTemp', 'AnimalAge', 'AnimalWeight', 'FlagSoln']
    cont_var_headers = ['JxnOffset', 'Temp', 'Age', 'Weight', 'FlagSoln']
    if getAllMetadata:
        for i in range(0, 5):
            cont_vars.extend(['external_%s_Mg' % i, 'external_%s_Ca' % i, 'external_%s_Na' % i, 'external_%s_Cl' % i, 'external_%s_K' % i, 'external_%s_pH' % i, 'external_%s_text' % i, 'internal_%s_Mg' % i, 'internal_%s_Ca' % i, 'internal_%s_Na' % i, 'internal_%s_Cl' % i, 'internal_%s_K' % i, 'internal_%s_pH' % i, 'internal_%s_text' % i])
            cont_var_headers.extend(['External_%s_Mg' % i, 'External_%s_Ca' % i, 'External_%s_Na' % i, 'External_%s_Cl' % i, 'External_%s_K' % i, 'External_%s_pH' % i, 'External_%s_text' % i, 'Internal_%s_Mg' % i, 'Internal_%s_Ca' % i, 'Internal_%s_Na' % i, 'Internal_%s_Cl' % i, 'Internal_%s_K' % i, 'Internal_%s_pH' % i, 'Internal_%s_text' % i])
    num_nom_vars = len(nom_vars)
    ephys_use_pks = range(1,28)

    ephys_list = m.EphysProp.objects.filter(pk__in = ephys_use_pks)
    ephys_headers = []
    for e in ephys_list:
        ephys_name_str = re.sub("[\s-]", "", e.name.title())
        ephys_headers.append(ephys_name_str)

    csvout = csv.writer(open(settings.OUTPUT_FILES_DIRECTORY + "article_ephys_metadata_curated.csv", "w+b"), delimiter = '\t')

    other_headers = ['NeuronType', 'Title', 'Journal', 'PubYear', 'PubmedLink', 'DataTableLinks', 'ArticleDataLink', 'LastAuthor']
    all_headers = other_headers
    all_headers.extend(ephys_headers)
    all_headers.extend(nom_vars + cont_var_headers)

    pubmed_base_link_str = 'http://www.ncbi.nlm.nih.gov/pubmed/%d/'
    table_base_link_str = 'http://neuroelectro.org/data_table/%d/'
    article_base_link_str = 'http://neuroelectro.org/article/%d/'

    csvout.writerow(all_headers)
    for a in articles:
        print "processing metadata for article: %s" % a.pk
        amdms = m.ArticleMetaDataMap.objects.filter(article = a)
        curr_metadata_list = ['']*(len(nom_vars) + len(cont_vars))
        for i,v in enumerate(nom_vars):
            valid_vars = amdms.filter(metadata__name = v)
            temp_metadata_list = [vv.metadata.value for vv in valid_vars]
            if 'in vitro' in temp_metadata_list and 'cell culture' in temp_metadata_list:
                curr_metadata_list[i] = 'cell culture'
            elif v == 'Strain' and amdms.filter(metadata__value = 'Mice').count() > 0:
                temp_metadata_list = 'C57BL'
                curr_metadata_list[i] = 'C57BL'
            elif v == 'Strain' and amdms.filter(metadata__value = 'Guinea Pigs').count() > 0:
                temp_metadata_list = 'Guinea Pigs'
                curr_metadata_list[i] = 'Guinea Pigs'
            elif len(temp_metadata_list) == 0 and v == 'Strain':
                if amdms.filter(metadata__value = 'Rats').count() > 0:
                    if np.random.randn(1)[0] > 0:
                        curr_metadata_list[i] = 'Sprague-Dawley'
                    else:
                        curr_metadata_list[i] = 'Wistar'
            elif len(temp_metadata_list) > 1:
                temp_metadata_list = temp_metadata_list[0]
                curr_metadata_list[i] = temp_metadata_list
            else:
                curr_metadata_list[i] = u'; '.join(temp_metadata_list)
        for i,v in enumerate(cont_vars):
            valid_vars = amdms.filter(metadata__name = v)
            if valid_vars.count() > 0:
                cont_value_ob = valid_vars[0].metadata.cont_value.mean
                curr_metadata_list[i+num_nom_vars] = cont_value_ob
            else:
                # check if
                if v == 'RecTemp' and amdms.filter(metadata__value = 'in vivo').count() > 0:
                    curr_metadata_list[i+num_nom_vars] = 37.0
                elif 'text' in v and ('external' in v or 'internal' in v):
                    for j in range(i - 6, i - 1, 1):
                        conc_amdm = amdms.filter(metadata__name = cont_vars[j])
                        if len(conc_amdm) > 0:
                            curr_metadata_list[i+num_nom_vars] = conc_amdm[0].metadata.ref_text.text.encode('utf8', "replace")
                            break
                        else:
                            curr_metadata_list[i+num_nom_vars] = 'NaN'
                else:
                    curr_metadata_list[i+num_nom_vars] = 'NaN'

# TODO: uncomment these 2 lines
        neurons = m.Neuron.objects.filter(Q(neuronconceptmap__times_validated__gte = 1) &
            ( Q(neuronconceptmap__source__data_table__article = a) | Q(neuronconceptmap__source__user_submission__article = a))).distinct()
        neurons = m.Neuron.objects.filter( Q(neuronconceptmap__source__data_table__article = a) | Q(neuronconceptmap__source__user_submission__article = a)).distinct()

        pubmed_link_str = pubmed_base_link_str % a.pmid
        article_link_str = article_base_link_str % a.pk
        dts = m.DataTable.objects.filter(article = a, datasource__neuronconceptmap__times_validated__gte = 1).distinct()
        if dts.count() > 0:
            dt_link_list = [table_base_link_str % dt.pk for dt in dts]
            dt_link_str = u'; '.join(dt_link_list)
        else:
            dt_link_str = ''

        #grandfather = define_ephys_grandfather(a)
        # grandfather = None
        # if grandfather is not None:
        #     grandfather_name = grandfather.lastname
        #     grandfather_name = grandfather_name.encode("iso-8859-15", "replace")
        # else:
        #     grandfather_name = ''
        last_author = get_article_last_author(a)
        if last_author is not None:
            last_author_name = '%s %s' % (last_author.last, last_author.initials)
            last_author_name = last_author_name.encode("utf8", "replace")
            # if grandfather_name is '':
            #     neuro_tree_node = get_neurotree_author(last_author)
            #     if neuro_tree_node is None:
            #         grandfather_name = 'Node not found'
        else:
            last_author_name = ''

        for n in neurons:
            curr_ephys_prop_list = []

            curr_ephys_prop_list.append(n.name)
            curr_ephys_prop_list.append((a.title).encode("utf8", "replace"))
            curr_ephys_prop_list.append(a.journal)
            curr_ephys_prop_list.append(a.pub_year)
            curr_ephys_prop_list.append(pubmed_link_str)
            curr_ephys_prop_list.append(dt_link_str)
            curr_ephys_prop_list.append(article_link_str)
            curr_ephys_prop_list.append(last_author_name)

            for e in ephys_list:
                curr_ephys_prop_list.append(computeArticleNedmSummary(a.pmid, n, e))

            curr_ephys_prop_list.extend(curr_metadata_list)
            #curr_ephys_prop_list.append(grandfather_name)

            csvout.writerow(curr_ephys_prop_list)
    return articles