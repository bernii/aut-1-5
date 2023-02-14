# import os, subprocess, time, sys

import os, sys, time
from subprocess import PIPE, Popen
from threading  import Thread
from queue import Queue, Empty
import signal

ON_POSIX = 'posix' in sys.builtin_module_names
IS_READY_OUTPUT = b"running on"
LAUNCH_ARGS = os.environ['LAUNCH_ARGS']

def enqueue_output(p_name):
  def handle(out, queue):
      for line in iter(out.readline, b''):
          sys.stdout.write(f"[{p_name}] > ")
          sys.stdout.write(line.decode('utf-8'))
          sys.stdout.flush()
          queue.put(line)
      out.close()
  return handle

def execute(command, name):
    print("Starting process - full command:", command)
    process = Popen(filter(None, command.split(" ")), stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX)
    queue = Queue()
    Thread(target=enqueue_output(name), args=(process.stdout, queue), daemon=True).start()
    Thread(target=enqueue_output(name), args=(process.stderr, queue), daemon=True).start()
    return process, queue


pid_aut, queue_aut = execute(f"python -u webui.py {LAUNCH_ARGS}", "webui")

# Poll process for new output until finished
while True:
    try:
        line = queue_aut.get(timeout=.1)
    except Empty:
        if pid_aut.poll() is not None:
            print("Process died, breaking loop")
            sys.exit('webui died on start, we\'re fucked!')
        # no output in that check
    else: # got line
        if IS_READY_OUTPUT in line:
            break # all good, continue
    # if longer > 60s
    # check if longer than 60s!! 

print('WebUI ready: Launching RunPod handler...')
pid_rp, queue_rp = execute('python -u /docker/runpod_infer.py', "runpod")

while True:
    if pid_rp.poll() is not None or pid_aut.poll() is not None:
        proc_name = "RunPod" if pid_rp.poll() is not None else "Aut1111"
        print(f"Process [{proc_name}] died somewhere, breaking loop")
        os.killpg(os.getpgid(pid_aut.pid), signal.SIGTERM)
        os.killpg(os.getpgid(pid_rp.pid), signal.SIGTERM)

#           File "/docker/reluncher.py", line 85, in <module>
#     os.killpg(os.getpgid(pid_rp.pid), signal.SIGTERM)
# ProcessLookupError: [Errno 3] No such process

        sys.exit('observed process died, exiting!')

    time.sleep(2)
