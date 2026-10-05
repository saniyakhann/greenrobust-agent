import json
import os
import sys
from llm import call_llm
from literature import search_genes, format_papers
from analyse import analyse

base = "/pfs/10/project/apptainer_cache/tu_iiodc01"

def find_counts_file(outdir):
    candidates = [
        os.path.join(outdir, "star_salmon", "salmon.merged.gene_counts.tsv"),
        os.path.join(outdir, "salmon", "salmon.merged.gene_counts.tsv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"no gene counts file found under {outdir}")

def pick_genes_to_search(up, down, n=5):
    prompt = f"""these features changed most in an experiment.

increased:
{up}

decreased:
{down}

pick the {n} most worth searching in the literature to understand the
underlying mechanism. prefer those whose function would explain the response.
reply with only a json list of names: ["name", "name"]"""
    raw = call_llm(prompt).strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def gather_literature(genes, context):
    results = search_genes(genes, context)
    blocks = []
    for gene, papers in results.items():
        if papers:
            blocks.append(f"literature for {gene}:\n{format_papers(papers)}")
    return "\n\n".join(blocks)

def refine_conclusion(conclusion, literature_text):
    prompt = f"""you previously drew this conclusion from experimental data:

{conclusion}

here is relevant published literature:

{literature_text[:12000]}

refine your conclusion using this literature. where the literature supports a
mechanism, cite the pmid. where it contradicts or complicates your reading, say so.
do not claim support that the abstracts do not provide."""
    return call_llm(prompt)

def build_hypothesis(question, comparison_label, refined, dataset):
    prompt = f"""you are producing a structured hypothesis about plant robustness.

question: {question}
comparison: {comparison_label}
dataset: {dataset}

refined conclusion:
{refined}

output only json in exactly this structure. every value must be your own
actual answer, not the placeholder text shown below - the placeholders only
describe what kind of answer is expected:

{{
  "claim": "directed mechanistic statement: [component] contributes to robustness against [stressor] in [species] via [mechanism]",
  "scope": {{
    "species": "",
    "stressor": "",
    "microbe_context": "n/a",
    "level": "molecular | cellular | tissue | organism"
  }},
  "support": {{
    "modality": "transcriptomics",
    "data_evidence": "which genes, what magnitude",
    "dataset": "{dataset}",
    "prior_knowledge": "cite pmids from the literature provided"
  }},
  "discriminating_prediction": {{
    "if_true": "what you would observe",
    "if_false": "what you would observe instead - must differ from if_true"
  }},
  "conservation": "would this hold in marchantia? reasoning",
  "confidence": "your actual confidence level (high, medium, or low) and your reasoning for it",
  "limitations": "what this data cannot establish"
}}"""
    return call_llm(prompt)

def generate(question, conclusion, findings_up, findings_down,
             comparison_label, context, dataset):
    genes = pick_genes_to_search(findings_up, findings_down)
    print("\nsearching literature for:", genes)

    literature_text = gather_literature(genes, context)
    refined = refine_conclusion(conclusion, literature_text)
    print("\nrefined conclusion:")
    print(refined)

    hypothesis = build_hypothesis(question, comparison_label, refined, dataset)
    print("\nstructured hypothesis:")
    print(hypothesis)
    return hypothesis


def run_full(question, mode="real"):
    from run_pipeline import select_and_run

    print("question:", question)
    run_result = select_and_run(question, mode=mode)
    print("\npipeline:", run_result["pipeline"])
    print("success:", run_result["success"])
    print("outdir:", run_result["outdir"])

    if not run_result["success"]:
        print("\npipeline failed, stopping here")
        print(run_result["stderr_tail"])
        return None

    counts_file = find_counts_file(run_result["outdir"])
    print("reading:", counts_file)
    result = analyse(question, counts_file,
                     f"{base}/fetchngs_all12/samplesheet/samplesheet_fixed.csv")
    print("\ndata conclusion:")
    print(result["conclusion"])

    return generate(
        question=question,
        conclusion=result["conclusion"],
        findings_up=result["up"],
        findings_down=result["down"],
        comparison_label=f"{result['treatment']} versus {result['baseline']}",
        context="arabidopsis heat stress",
        dataset="GSE300558",
    )
if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "how does arabidopsis respond to heat stress?"
    run_full(question)
