# Chunky Deployment Workflow

This is the lower-friction path for running Memex-SR on
`chunky.csail.mit.edu`.

The goal is to reduce repeated setup work. It does not bypass Duo,
Kerberos, AFS, Docker permissions, or CSAIL policy.

## Local SSH Setup

On your laptop, add a host alias with SSH connection reuse:

```sshconfig
Host chunky
  HostName chunky.csail.mit.edu
  User mohoney
  ControlMaster auto
  ControlPersist 8h
  ControlPath ~/.ssh/cm-%r@%h:%p
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

The first `ssh chunky` may still require Duo. Additional `ssh`, `scp`,
and `rsync` commands reuse the existing control connection while it is
alive.

If your local OpenSSH and CSAIL account support Kerberos delegation, you
can try this optional block:

```sshconfig
Host chunky-gssapi
  HostName chunky.csail.mit.edu
  User mohoney
  GSSAPIAuthentication yes
  GSSAPIDelegateCredentials yes
  ControlMaster auto
  ControlPersist 8h
  ControlPath ~/.ssh/cm-%r@%h:%p
```

That can reduce server-side `kinit` prompts when you already have a
local CSAIL Kerberos ticket, but it depends on client/server GSSAPI
support.

## Use A Persistent Shell

After login:

```bash
tmux new -A -s memex-sr
```

This keeps long bootstrap, parse, and download jobs alive if the laptop
disconnects.

## Fast Path

After login, use one command from any Engram checkout:

```bash
bash deployments/memex-sr/scripts/deploy_chunky.sh --install-uv
```

The deploy wrapper:

- moves work to `/data1/$USER/projects/mit/Engram` when needed;
- clones Engram if the local-disk checkout does not exist;
- fetches `fork/codex/systems-researcher-okg`;
- updates submodules;
- refreshes Kerberos/AFS credentials;
- bootstraps Postgres/OKG;
- migrates, loads the catalog, ingests, publishes, and prints status;
- generates `deployments/memex-sr/reports/cloudcast-ab/context-packet-chunky.md`.

Preflight only:

```bash
bash deployments/memex-sr/scripts/deploy_chunky.sh --check-only
```

If you need to use an existing Postgres instead of Docker:

```bash
MEMEX_SR_OKG_DSN=postgres://USER:PASS@HOST:PORT/DB \
  bash deployments/memex-sr/scripts/deploy_chunky.sh --skip-docker
```

## Manual Local-Disk Checkout

AFS home directories need Kerberos/AFS tokens for writes. Long-running
jobs are less fragile from local disk. The fast path does this
automatically, but the manual commands are:

```bash
mkdir -p /data1/"$USER"/projects/mit
cd /data1/"$USER"/projects/mit
git clone --recurse-submodules https://github.com/mit-nms/Engram.git
cd Engram
git remote add fork https://github.com/JasonMoho/Engram.git 2>/dev/null || true
git fetch fork
git switch codex/systems-researcher-okg
git pull --ff-only fork codex/systems-researcher-okg
git submodule update --init --recursive
```

Then run the lower-level bootstrap:

```bash
bash deployments/memex-sr/scripts/bootstrap_chunky.sh --install-uv
```

Preflight only:

```bash
bash deployments/memex-sr/scripts/bootstrap_chunky.sh --check-only
```

If Docker access is still blocked, the script will stop with the same
admin-facing message as `bootstrap_local.sh`. That part requires CSAIL
admin action, for example adding the user to the Docker group and
logging out/back in.

## Daily Refresh

```bash
ssh chunky
tmux new -A -s memex-sr
cd /data1/"$USER"/projects/mit/Engram
bash deployments/memex-sr/scripts/deploy_chunky.sh
```

If credentials have expired, the wrapper prompts for `kinit` and refreshes
AFS tokens. If credentials are still valid, it skips the prompt.

## Why `chmod` Did Not Fix AFS Writes

On AFS, Unix mode bits are not enough. You also need a valid Kerberos
ticket and AFS token:

```bash
klist
tokens
kinit "$USER@CSAIL.MIT.EDU"
aklog csail.mit.edu
```

If `tokens` shows no CSAIL token, writes under `/afs/csail.mit.edu/...`
can fail even when `ls -l` looks permissive.
