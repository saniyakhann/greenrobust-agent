from llm import call_llm
from nfclaw_tool import run_nfclaw

base = "/pfs/10/project/apptainer_cache/tu_iiodc01"
home = "/home/tu/tu_tu/tu_iiodc01"

import csv

def describe_data(samplesheet):
    rows = []
    with open(samplesheet, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "no data description available"

    first = rows[0]
    strategy = first.get("library_strategy", "unknown")
    layout = first.get("library_layout", "unknown")
    organism = first.get("scientific_name", "unknown")
    titles = [r.get("sample_title", "") for r in rows]

    return (f"{len(rows)} samples of {strategy} data from {organism}, "
            f"{layout.lower()} layout. sample titles: {'; '.join(titles[:12])}")


def get_pipelines():
    return run_nfclaw(["list"])["stdout"]

def choose_pipeline(question, pipelines, data_description):
    prompt = f"""you are a bioinformatics assistant choosing a pipeline to run.

the available data: {data_description}

available nf-core pipelines:
{pipelines[:8000]}

user question: {question}

choose the single pipeline that fits this data and question. prefer general
purpose pipelines over specialised ones unless the question specifically calls
for the specialism.

reply with only the pipeline name, nothing else."""
    return call_llm(prompt).strip()

def build_args(pipeline, outdir, mode):
    if mode == "demo":
        return [
            "run", pipeline,
            "--demo",
            "-profile", "test,binac2",
            "--outdir", outdir,
            "--nxf-ver", "25.04.3",
        ]
    return [
        "run", pipeline,
        "--input", f"{base}/fetchngs_all12/samplesheet/samplesheet_fixed.csv",
        "--outdir", outdir,
        "--fasta", f"{home}/Arabidopsis_thaliana.TAIR10.dna.toplevel.fa",
        "--gtf", f"{home}/Arabidopsis_thaliana.TAIR10.52.gtf",
        "-profile", "binac2",
        "--nxf-ver", "25.04.3",
    ]

def select_and_run(question, mode="demo"):
    pipelines = get_pipelines()
    data_description = describe_data(f"{base}/fetchngs_all12/samplesheet/samplesheet_fixed.csv")
    print("data:", data_description)
    choice = choose_pipeline(question, pipelines, data_description)
    print("llm chose:", choice)

    outdir = f"{base}/agent_run_{choice}_{mode}"
    args = build_args(choice, outdir, mode)
    print("running:", " ".join(["nfclaw"] + args))

    result = run_nfclaw(args)
    return {
        "pipeline": choice,
        "success": result["success"],
        "outdir": outdir,
        "stdout_tail": result["stdout"][-2000:],
        "stderr_tail": result["stderr"][-2000:],
    }

if __name__ == "__main__":
    question = "i want to analyse gene expression changes in arabidopsis under heat stress"
    result = select_and_run(question, mode="demo")

    print("\npipeline:", result["pipeline"])
    print("success:", result["success"])
    print("outdir:", result["outdir"])
    print("\noutput tail:")
    print(result["stdout_tail"])
