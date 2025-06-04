import os, sys, subprocess, time, select, platform
from pathlib import Path

try:
    from IPython.display import HTML, display # used to display the progress in the IPython notebook
    def stdout(msg):
        if msg:
            display(HTML("<pre style=\"color:green\">" + msg  + "</pre>"))
            
    def stderr(msg):
        if msg:
            display(HTML("<pre style=\"color:red\">" + msg + "</pre>"))

except ImportError:
    def stdout(msg):
        sys.stdout.write(msg)
            
    def stderr(msg):
        sys.stderr.write(msg)

import IPython

def runrotalumis(model_file, output_directory, library_paths=[]):
    """model is a path to a model (relative to the rotalumis executable, or absolute)
    The runner will execute the model and print the output to the IPython/Jupyter notebook.
    Returns the exit code of the Rotalumis process
    """
    basedir = os.path.abspath(os.path.dirname(str(__file__)))
    returncode = -1
    
    prev_dir = os.getcwd()
    
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    returnerror = ""
    
    try:
        if platform.system() == "Linux":
            rotalumis_bin = os.path.join(basedir, "rotalumis")
        else:
            rotalumis_bin = os.path.join(basedir, "rotalumis.exe")
        if not os.path.isfile(rotalumis_bin):
            raise Exception(f"Could not locate Rotalumis in {rotalumis_bin}")
            
        if not os.path.isabs(model_file):
            inputmodel = os.path.join(prev_dir, model_file)
        else:
            inputmodel = model_file

        lib_includes = []
        
        for l in library_paths:
            lib_includes += ["-I", l]

        os.chdir(output_directory) # make sure the outputs are going into this folder!                    
        
        is_interactive = IPython.get_ipython() is not None
        is_interactive = False
        args = [rotalumis_bin, '--stdlib', '--poosl', inputmodel] + lib_includes
        
        if is_interactive:
            try:
                p = subprocess.Popen(args + lib_includes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                while p.poll() is None:
                    stdout(p.stdout.read().decode('utf-8'))
                    stderr(p.stderr.read().decode('utf-8'))
                    time.sleep(0.1)
            finally:
                p.terminate()
        else: 
            p = subprocess.run(args, capture_output=True, encoding='utf-8')
            with open("stdout.txt", "w", newline='') as f:
                f.write(p.stdout)
            with open("stderr.txt", "w", newline='') as f:
                f.write(p.stderr)

            if p.returncode != 0 and Path("stderr.txt").exists():
                with open("stderr.txt", "r") as f:
                    returnerror = f.read()
        returncode = p.returncode
    finally:
        # always put the current working directory back!
        os.chdir(prev_dir)
        
    return returncode, returnerror
    
if __name__ == "__main__":    
    runrotalumis(sys.argv[1], sys.argv[2], sys.argv[3:])
