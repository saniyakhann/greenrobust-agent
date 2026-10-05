import csv
import json
import math
import pandas as pd
from llm import call_llm

base = "/pfs/10/project/apptainer_cache/tu_iiodc01"

def read_sample_titles(samplesheet):
    titles = {}
    with open(samplesheet, newline="") as f:
        for row in csv.DictReader(f):
            sid = row.get("sample")
            if sid:
                titles[sid] = row.get("sample_title", "")
    return titles

def infer_groups(titles):
    listing = "\n".join(f"{sid}: {t}" for sid, t in titles.items())
    prompt = f"""these are rna-seq samples and their titles:

{listing}

group the samples by experimental condition. samples that are replicates of the
same condition belong in one group.

reply with only json, no other text, in this form:
{{"group_name": ["sample_id", "sample_id"], "group_name": ["sample_id"]}}"""
    raw = call_llm(prompt).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def choose_comparison(question, groups):
    prompt = f"""available experimental groups: {list(groups.keys())}

user question: {question}

which two groups should be compared to answer this question?
reply with only json: {{"baseline": "group", "treatment": "group"}}"""
    raw = call_llm(prompt).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def compare(df, groups, baseline, treatment, top_n=15, min_counts=100):
    a = df[groups[baseline]].mean(axis=1)
    b = df[groups[treatment]].mean(axis=1)
    res = pd.DataFrame({"gene": df["gene_name"], "mean_a": a.round(1), "mean_b": b.round(1)})
    res = res[(res["mean_a"] + res["mean_b"]) > min_counts].copy()
    res["log2fc"] = [round(math.log2((y + 1) / (x + 1)), 2)
                     for x, y in zip(res["mean_a"], res["mean_b"])]
    return res.nlargest(top_n, "log2fc"), res.nsmallest(top_n, "log2fc")

def format_genes(rows, name_a, name_b):
    return "\n".join(
        f"{r['gene']}: {name_a}={r['mean_a']}, {name_b}={r['mean_b']}, log2fc={r['log2fc']}"
        for _, r in rows.iterrows()
    )

def draw_conclusion(question, baseline, treatment, up, down):
    prompt = f"""you are a plant biologist analysing rna-seq data.

question: {question}
comparison: {treatment} versus {baseline}

genes most increased in {treatment}:
{format_genes(up, baseline, treatment)}

genes most decreased in {treatment}:
{format_genes(down, baseline, treatment)}

what biological processes are changing, and what does this suggest about how the
plant responds to this condition? be specific about which genes support each point.
state clearly what the data cannot establish. do not speculate beyond the data."""
    return call_llm(prompt)

def analyse(question, counts_file, samplesheet):
    titles = read_sample_titles(samplesheet)
    groups = infer_groups(titles)
    print("groups:", groups)

    comparison = choose_comparison(question, groups)
    baseline, treatment = comparison["baseline"], comparison["treatment"]
    print("comparing:", treatment, "vs", baseline)

    df = pd.read_csv(counts_file, sep="\t")
    up, down = compare(df, groups, baseline, treatment)

    conclusion = draw_conclusion(question, baseline, treatment, up, down)

    return {
        "question": question,
        "groups": groups,
        "baseline": baseline,
        "treatment": treatment,
        "up": format_genes(up, baseline, treatment),
        "down": format_genes(down, baseline, treatment),
        "conclusion": conclusion,
    }

if __name__ == "__main__":
    result = analyse(
        "how does arabidopsis respond to heat stress?",
        f"{base}/rnaseq_all12_results/star_salmon/salmon.merged.gene_counts.tsv",
        f"{base}/fetchngs_all12/samplesheet/samplesheet_fixed.csv",
    )
    print("\nconclusion:")
    print(result["conclusion"])
