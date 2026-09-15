import subprocess

def run_nfclaw(args):
    cmd = ["nfclaw"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }
