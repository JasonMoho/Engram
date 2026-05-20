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

## Prefer Local Disk For The Checkout

AFS home directories need Kerberos/AFS tokens for writes. Long-running
jobs are less fragile from local disk:

```bash
mkdir -p /data1/"$USER"
cd /data1/"$USER"
git clone --recurse-submodules https://github.com/mit-nms/Engram.git
cd Engram
```

If `/data1/$USER` is not writable, use `~/src/Engram`, but expect to
refresh tokens after login.

For the current development branch:

```bash
git remote add fork https://github.com/JasonMoho/Engram.git 2>/dev/null || true
git fetch fork
git switch codex/systems-researcher-okg
git pull --ff-only fork codex/systems-researcher-okg
git submodule update --init --recursive
```

## One Command On Chunky

From the Engram repo root:

```bash
bash deployments/memex-sr/scripts/bootstrap_chunky.sh --install-uv
```

What it does:

- checks Kerberos with `klist`;
- runs `kinit` only when no ticket is present;
- runs `aklog csail.mit.edu` when available;
- verifies AFS home write access when `$HOME` is under `/afs`;
- updates submodules;
- calls `bootstrap_local.sh` to run the normal Memex-SR bootstrap.

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
cd /data1/"$USER"/Engram
git pull --ff-only fork codex/systems-researcher-okg
git submodule update --init --recursive
bash deployments/memex-sr/scripts/bootstrap_chunky.sh
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
