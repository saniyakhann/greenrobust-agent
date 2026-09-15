#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=4:00:00
#SBATCH --mem=64G
#SBATCH --job-name=agent_run
#SBATCH --output=/pfs/10/project/apptainer_cache/tu_iiodc01/agent/agent_run_%j.log

module load cs/ollama
module load devel/python/3.12_gnu_11.4
module load devel/java_jdk/21.0.2
export PATH=/home/tu/tu_tu/tu_iiodc01:$PATH
export OLLAMA_MODELS=/pfs/10/project/apptainer_cache/tu_iiodc01/ollama_models
export APPTAINER_TMPDIR=/pfs/10/project/apptainer_cache/tu_iiodc01/tmp
export APPTAINER_CACHEDIR=/pfs/10/project/apptainer_cache/tu_iiodc01
export NXF_WORK=/pfs/10/project/apptainer_cache/tu_iiodc01/nxf_work_agent

ollama serve &
sleep 15

cd /pfs/10/project/apptainer_cache/tu_iiodc01/agent
python3 hypothesis.py
