# Python safe_exec + seccomp cheat-sheet
* Use `subprocess.run([...], preexec_fn=seccomp_sandbox, ...)`
* Limit resources with `resource.setrlimit`.
