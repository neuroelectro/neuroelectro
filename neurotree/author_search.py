# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 16:36:21 2013

@author: Shreejoy
"""
import sys

from django.db.models import Q

from db_functions.author_search import get_article_last_author
import neurotree.models as t
from helpful_functions.prog import prog
import neuroelectro.models as m

# this gets all articles which have some nedms in neuroelectro

def get_neurotree_authors():
    """
    Returns a list of NeuroTree author nodes corresponding to last authors 
    of NeuroElectro articles.
    Also returns statistics based on how many NeuroElectro authors had 
    corresponding entries in NeuroTree
    """
    
    q1 = Q(datatable__datasource__neuronconceptmap__times_validated__gte=1)
    q2 = Q(usersubmission__datasource__neuronconceptmap__times_validated__gte=1)
    articles = m.Article.objects.filter(q1 | q2).distinct()
        
    found_count = 0
    cant_resolve_count = 0
    cant_find_count = 0
    last_author_node_list = []
    for i,article in enumerate(articles):
        print i
#        print article
#        print article.author_list_str
        author_ob = get_article_last_author(article)
        if not author_ob:
            print 'Article %s does not have an author list string' % \
                    article.title
            cant_find_count += 1
            last_author_node_list.append(None)
            continue
        last_name = author_ob.last
        first_name = author_ob.first.split()[0]
        # get neurotree author object corresponding to pubmed author object
        a_node_query = t.Node.objects.filter(lastname = last_name)
        if a_node_query.count() > 0: # checks that 
            a_node_query = t.Node.objects.filter(lastname = last_name,
                                    firstname__icontains = first_name[0])
            if a_node_query.count() > 1:
                a_node_query = t.Node.objects.filter(lastname = last_name, 
                                            firstname__icontains = first_name)
                if a_node_query.count() > 1: 
                    print 'Author: %s, %s has too many identical nodes \
                           in NeuroTree' % (last_name, first_name)
                    cant_resolve_count += 1
                    last_author_node_list.append(None)
        if a_node_query.count() ==0:
            print 'Author: %s, %s not in NeuroTree' % \
                    (last_name, first_name)
            cant_find_count += 1
        if a_node_query.count() == 1:
            #################################################
            # author_node is author variable in neuro tree  #
            #################################################
            author_node = a_node_query[0]
            last_author_node_list.append(author_node)

            print 'Author: %s, found in NeuroTree' % author_node
            found_count += 1
        print 'a'
            
    authors = []
    none_count = 0
    duplicate_count = 0
    for author in last_author_node_list:
        if author not in authors:
            if author is not None:
                authors.append(author)
            else:
                none_count += 1
                found_count -= 1
        else:
            duplicate_count += 1
            found_count -= 1

    return (authors, found_count, cant_resolve_count, 
            cant_find_count, duplicate_count, none_count)


def get_neurotree_author(author_ob):
    """
    Gets the NeuroTree author object node given a NeuroElectro author object

    Because of ambiguities resoloving author names, 
    it'll return None if it can't resolve author name (as from pubmed)
    """
    last_name = author_ob.last
    first_name = author_ob.first.split()[0]
    # get neurotree author object corresponding to pubmed author object
    a_node_query = t.Node.objects.filter(lastname = last_name)
    if a_node_query.count() > 1:
        a_node_query = t.Node.objects.filter(lastname = last_name, 
                                        firstname__icontains = first_name[0])
        if a_node_query.count() > 1:
            a_node_query = t.Node.objects.filter(lastname = last_name, 
                                            firstname__icontains = first_name)
            if a_node_query.count() > 1: 
                #print 'Author: %s, %s has too many \
                #       identical nodes in NeuroTree' % (last_name, first_name)
                #cant_resolve_count += 1
                #last_author_node_list.append(None)
                return None
    if a_node_query.count() ==0:
        #print 'Author: %s, %s not in NeuroTree'  % (last_name, first_name)
        #cant_find_count += 1
        return None
    if a_node_query.count() == 1:
        #################################################
        # author_node is author variable in neuro tree  #
        #################################################
        author_node = a_node_query[0]
        #print 'Author: %s, found in NeuroTree' % author_node
        return author_node
        #last_author_node_list.append(author_node)        
        #found_count += 1

def get_author_grandparents(authors):
    """
    Returns a list of neurotree nodes corresponding to academic 
    grandparents of input neurotree nodes
    """
    author_list_initial = authors
    num_authors = len(authors)
    author_list_final = []
    relationcodes = [1, 2]
    for i,a in enumerate(author_list_initial):
        prog(i,num_authors)
        a_relations = a.parents.filter(relationcode__in=relationcodes)
        parent_nodes = [x.node2 for x in a_relations]
        #print parent_nodes
        author_list_final.extend(parent_nodes)
        for p in parent_nodes:
            p_relations = p.parents.filter(relationcode__in=relationcodes)
            grand_parent_nodes = [y.node2 for y in p_relations]
            author_list_final.extend(grand_parent_nodes)
    author_list_final.extend(author_list_initial)
    return list(set(author_list_final))
    
def prog(num,denom):
    fract = float(num)/denom
    hyphens = int(round(50*fract))
    spaces = int(round(50*(1-fract)))
    sys.stdout.write('\r%.2f%% [%s%s]' % (100*fract,'-'*hyphens,' '*spaces))
    sys.stdout.flush() 