import json
import urllib.parse
import urllib.request

api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def search(query, limit=5):
    params = urllib.parse.urlencode({
        "query": query,
        "format": "json",
        "pageSize": limit,
        "resultType": "core",
    })
    url = f"{api}?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)

    papers = []
    for item in data.get("resultList", {}).get("result", []):
        papers.append({
            "title": item.get("title", ""),
            "abstract": item.get("abstractText", ""),
            "year": item.get("pubYear", ""),
            "journal": item.get("journalTitle", ""),
            "pmid": item.get("pmid", ""),
            "doi": item.get("doi", ""),
        })
    return papers

def format_papers(papers, abstract_chars=600):
    blocks = []
    for p in papers:
        abstract = (p["abstract"] or "")[:abstract_chars]
        blocks.append(
            f"title: {p['title']}\n"
            f"journal: {p['journal']} ({p['year']})\n"
            f"pmid: {p['pmid']}\n"
            f"abstract: {abstract}"
        )
    return "\n\n".join(blocks)

def search_genes(genes, context, per_gene=3):
    results = {}
    for gene in genes:
        query = f"{gene} AND {context}"
        try:
            results[gene] = search(query, limit=per_gene)
        except Exception as e:
            results[gene] = []
            print(f"search failed for {gene}: {e}")
    return results
