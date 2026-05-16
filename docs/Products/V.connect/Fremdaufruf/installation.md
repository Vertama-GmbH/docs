# V.connect Fremdaufruf — Installation Manual

This manual covers installing, configuring, and operating the
V.connect Fremdaufruf Service on a KIS workstation. Audience:
system administrators responsible for the workstation. For the
KIS-integrator-facing walkthrough of the URL-builder tooling, see
the [Benutzerhandbuch](user-manual.md).

---

## 1. Prerequisites

| Item                          | Requirement                                                                                |
|-------------------------------|--------------------------------------------------------------------------------------------|
| **Platform**                  | Windows 10 or later (x64); Linux x86-64 or ARM64 (systemd-based distribution); macOS for development. |
| **Outbound network**          | HTTPS reachability from the workstation to the V.ap base URL.                              |
| **V.ap API user**             | Provisioned by your Vertama contact, with the module scopes the integration requires.      |
| **Service-installation rights** | Administrator (Windows) or root (Linux) for service registration. Day-to-day operation runs as an unprivileged service account. |
| **Disk**                      | < 50 MB for the binary, configuration, and audit log. Plan additional capacity if you direct the audit log to a file and operate at high request volume. |

The component is a single static binary with no runtime
dependencies on the workstation — no JRE, no .NET runtime, no
shared libraries beyond the OS itself.

---

## 2. Installation

### 2.1 Windows

The recommended path is the **signed MSI installer**: it places the
binary, registers the Windows service, and writes the configuration
template to `%PROGRAMDATA%\Vertama\fremdaufruf\`. Authenticode
signature can be verified before install via the file's *Digital
Signatures* tab.

If your environment prohibits MSI installation or you prefer manual
deployment, the binary can be installed directly:

1. Copy `fremdaufruf.exe` to `%PROGRAMFILES%\Vertama\fremdaufruf\`.
2. Register a Windows service. With `sc.exe`:

    ```bat
    sc create Fremdaufruf binPath= "\"%PROGRAMFILES%\Vertama\fremdaufruf\fremdaufruf.exe\" -config \"%PROGRAMDATA%\Vertama\fremdaufruf\config.toml\"" start= auto displayname= "V.connect Fremdaufruf"
    sc description Fremdaufruf "Local bridge for KIS GET-only integration with V.ap"
    ```

    Alternatively, with [NSSM](https://nssm.cc/) — useful for richer
    log handling and restart policies:

    ```bat
    nssm install Fremdaufruf "%PROGRAMFILES%\Vertama\fremdaufruf\fremdaufruf.exe"
    nssm set Fremdaufruf AppParameters "-config \"%PROGRAMDATA%\Vertama\fremdaufruf\config.toml\""
    nssm set Fremdaufruf Start SERVICE_AUTO_START
    ```

3. Create the configuration directory:

    ```bat
    mkdir "%PROGRAMDATA%\Vertama\fremdaufruf"
    ```

    and write `config.toml` per [§3](#3-configuration). Restrict its
    ACL to the service account.

4. Start the service:

    ```bat
    sc start Fremdaufruf
    ```

### 2.2 Linux

Distributed as a tarball containing the binary, a systemd unit, and
a configuration template.

1. Extract:

    ```bash
    sudo tar -xzf fremdaufruf-1.0.0-linux-amd64.tar.gz -C /tmp
    sudo install -m 0755 /tmp/fremdaufruf/fremdaufruf /usr/local/bin/
    sudo install -d /etc/vertama/fremdaufruf
    sudo install -m 0600 /tmp/fremdaufruf/config.example.toml \
        /etc/vertama/fremdaufruf/config.toml
    sudo install -m 0644 /tmp/fremdaufruf/fremdaufruf.service \
        /etc/systemd/system/
    ```

2. Edit `/etc/vertama/fremdaufruf/config.toml` per
   [§3](#3-configuration).

3. Enable and start:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable --now fremdaufruf
    sudo systemctl status fremdaufruf
    ```

The shipped systemd unit runs the service as a dedicated unprivileged
user (`fremdaufruf`) which the unit creates on first start.

### 2.3 macOS (development only)

macOS is supported for development. Install the binary into
`/usr/local/bin/`, place `config.toml` at
`/usr/local/etc/vertama/fremdaufruf/config.toml`, and run the binary
in the foreground or under your preferred process manager (e.g.
`launchd`). macOS is not a supported production deployment target.

---

## 3. Configuration

The component reads a TOML file. This section covers the schema,
file permissions, and environment-variable override convention.

### 3.1 File location

| Platform | Default path                                              |
|----------|-----------------------------------------------------------|
| Windows  | `%PROGRAMDATA%\Vertama\fremdaufruf\config.toml`           |
| Linux    | `/etc/vertama/fremdaufruf/config.toml`                    |
| macOS    | `/usr/local/etc/vertama/fremdaufruf/config.toml`          |

Override at startup with the `-config <path>` flag or the
`FREMDAUFRUF_CONFIG` environment variable. Flag takes precedence
over env, which takes precedence over the platform default.

### 3.2 Schema

```toml
vap_base_url = "https://elim.example.com"   # required; MUST be https://
api_user     = "lab-api"                    # required; provisioned by Vertama
api_secret   = "<password>"                 # required; provisioned by Vertama

[bind]
address = "127.0.0.1"                       # default: 127.0.0.1
port    = 8810                              # default: 8810

[http]
request_timeout = "10s"                     # Go duration string; default: 10s
connect_timeout = "3s"                      # default: 3s
tls_verify      = true                      # default: true; false permitted for dev only

[allowlist]
# Optional. When present and non-empty, requests whose upstream
# path is not on the list are rejected with 404 path_not_allowed,
# before any upstream call. Each entry must be an absolute path
# (start with '/'); matching is verbatim — no glob, no trailing-
# slash normalisation, no case folding.
paths = [
    "/api/duba/v1/memento",
    "/api/elimplus/v1/memento",
]

[access]
# Required when bind.address is not a loopback address (i.e. for
# intranet-bound deployments). When set, every request must carry
# a matching `_s` URL parameter; on mismatch the component returns
# 403. Leave unset for loopback-only deployments.
secret = ""

[log]
level       = "info"                        # debug | info | warn | error
destination = "stderr"                      # stderr | file (V1; syslog/eventlog planned)
file_path   = "/var/log/vertama/fremdaufruf.log"   # required if destination = "file"
```

Required fields: `vap_base_url`, `api_user`, `api_secret`. The
service refuses to start without them.

The service also refuses to start on any of:

- `vap_base_url` not absolute or not `https://` (HTTP is allowed
  only when `tls_verify = false`, intended for dev-only against a
  self-signed V.ap).
- `bind.address` not a valid IP.
- `bind.port` outside `[1, 65535]`.
- `bind.address` is **not a loopback address AND `[access] secret`
  is unset or empty**. Intranet-bound deployments require an
  access secret as their trust boundary.
- `[allowlist] paths` contains an entry that does not start with
  `/` (each entry must be an absolute path).
- `log.destination = "file"` without `log.file_path`, or a path
  the service account cannot write.
- `log.destination = "eventlog"` on a non-Windows platform.

The component does not support hot reload. Configuration changes
require a service restart.

### 3.3 File permissions

The component refuses to read a config file that is readable by
group or other.

```bash
sudo chmod 0600 /etc/vertama/fremdaufruf/config.toml
sudo chown fremdaufruf:fremdaufruf /etc/vertama/fremdaufruf/config.toml
```

On Windows the equivalent NTFS ACL check is performed — the
recommended ACL is read access for the service account and admin
group only.

### 3.4 Environment-variable overrides

Every config field can be overridden by an environment variable.
Useful for secrets-management systems that inject secrets at
service start time rather than at rest in a file. Precedence is
**env > file > built-in default**.

| Field                    | Environment variable                  |
|--------------------------|---------------------------------------|
| `vap_base_url`           | `FREMDAUFRUF_VAP_BASE_URL`            |
| `api_user`               | `FREMDAUFRUF_API_USER`                |
| `api_secret`             | `FREMDAUFRUF_API_SECRET`              |
| `bind.address`           | `FREMDAUFRUF_BIND_ADDRESS`            |
| `bind.port`              | `FREMDAUFRUF_BIND_PORT`               |
| `http.request_timeout`   | `FREMDAUFRUF_HTTP_REQUEST_TIMEOUT`    |
| `http.connect_timeout`   | `FREMDAUFRUF_HTTP_CONNECT_TIMEOUT`    |
| `http.tls_verify`        | `FREMDAUFRUF_HTTP_TLS_VERIFY`         |
| `allowlist.paths`        | `FREMDAUFRUF_ALLOWLIST_PATHS` (comma-separated, e.g. `"/a,/b"`) |
| `access.secret`          | `FREMDAUFRUF_ACCESS_SECRET`           |
| `log.level`              | `FREMDAUFRUF_LOG_LEVEL`               |
| `log.destination`        | `FREMDAUFRUF_LOG_DESTINATION`         |
| `log.file_path`          | `FREMDAUFRUF_LOG_FILE_PATH`           |

Additionally, `FREMDAUFRUF_CONFIG` specifies the path to the
configuration file, overriding the platform default; the
`-config <path>` flag takes precedence over `FREMDAUFRUF_CONFIG`.

At startup the service logs each effective configuration field
with its source (`from file`, `from env`, or `from default`).
`api_secret` and `[access] secret` are included in the source
tracking but their values are never printed.

---

## 4. First start

After the service is installed and the configuration is in place,
work through these checks before adding any KIS configuration:

### 4.1 Verify the service is running

| Platform | Command                                           |
|----------|---------------------------------------------------|
| Windows  | `sc query Fremdaufruf` or *Services* MMC          |
| Linux    | `systemctl status fremdaufruf`                    |

Service state should be **running**. The first log lines show the
effective configuration with provenance markers (`from file`,
`from env`, `from default`); `api_secret` is shown as `***`.

### 4.2 Verify V.ap reachability

From the workstation:

```bash
curl -i https://elim.example.com/api/<module>/v1/memento -u "lab-api:<password>"
```

You should get an HTTP 4xx response (the call is malformed — no
JSON body), but **the response must come from V.ap, not from a
proxy or firewall**. Confirm the response headers identify V.ap.
If you see a connect timeout, a 5xx from an intermediate proxy, or
a TLS handshake failure, fix that before continuing — the
component will run into the same failure mode at runtime.

### 4.3 End-to-end smoke test

With a URL template you generated via the V.ap URL-builder tooling
(see the [Benutzerhandbuch](user-manual.md)), fire the request
against the local component:

```bash
curl -i "http://127.0.0.1:8810/l/api/<module>/v1/memento?..."
```

Expected response: **303 See Other** with a `Location` header
pointing at `<vap_base_url><magicLink>`. Open the `Location` URL in
a browser — you should land on the pre-filled form.

If you see a 400, 422, or 502 instead, see
[§6 Troubleshooting](#6-troubleshooting).

---

## 5. Operation

### 5.1 Audit log

The component writes one JSON line per inbound request, structured
for machine parsing. Each line carries:

| Field             | Always present | Description                                    |
|-------------------|----------------|------------------------------------------------|
| `ts`              | yes            | RFC 3339 timestamp, UTC, millisecond precision |
| `version`         | yes            | Component version                              |
| `method`          | yes            | Always `"GET"` in V1                           |
| `path`            | yes            | Request path, query string stripped            |
| `param_count`     | yes            | Number of data parameters after meta-strip     |
| `coerce`          | yes            | `"ok"` or `"err"`                              |
| `upstream_path`   | when reached   | Path used in the outbound POST                 |
| `upstream_status` | when reached   | HTTP status returned by V.ap                   |
| `status`          | yes            | HTTP status returned to caller                 |
| `dur_ms`          | yes            | End-to-end handling duration, milliseconds     |
| `error`           | on error       | Stable error code                              |

Destination is configured by `log.destination`:

| `log.destination` | Behavior                                                                          |
|-------------------|-----------------------------------------------------------------------------------|
| `stderr`          | Written to standard error. Captured by the service manager (journald on Linux, Windows Event Log via NSSM, or to a configured stderr-redirect file). Default. |
| `file`            | Written to the path in `log.file_path`. The file is created with owner-only permissions and opened in append mode. |
| `syslog`          | Planned. Not implemented in V1; the component fails to start with a clear error if configured. |
| `eventlog`        | Planned. Not implemented in V1; same behavior as `syslog` above.                  |

**Log rotation** is the operator's responsibility. The component
itself does not rotate. On Linux, use `logrotate` with a `copytruncate`
strategy (the component holds the file handle in append mode). On
Windows under NSSM, use NSSM's built-in rotation settings.

**Privacy guarantee.** The audit log never contains:

- Data-parameter **values** (patient names, dates, IDs, anything
  the KIS substituted into the URL).
- Data-parameter **keys** (which fields were carried).
- The configured `api_secret`.

Only the **count** of data parameters and structural information
(HTTP status, duration, upstream status, error code) is recorded.
This guarantee is enforced by the component and verified by its
test suite.

### 5.2 Health checking

V1 does not expose a dedicated health endpoint. Use the service
manager for liveness:

| Platform | Liveness check                                                |
|----------|---------------------------------------------------------------|
| Windows  | `sc query Fremdaufruf` — STATE should be `RUNNING`            |
| Linux    | `systemctl is-active fremdaufruf` — should return `active`    |

For HTTP-level reachability from a monitoring system on the same
workstation, a GET to any non-`/l/` path returns 404 in well under
10 ms; that round-trip confirms the listener is alive.

### 5.3 Updates

V1 does not support hot reload. Configuration changes and binary
updates both require a service restart:

```bash
# Linux
sudo systemctl restart fremdaufruf

# Windows
sc stop Fremdaufruf && sc start Fremdaufruf
```

For binary updates, replace `fremdaufruf` / `fremdaufruf.exe` on
disk first, then restart. The restart takes well under a second;
in-flight requests complete before the old process exits (graceful
shutdown).

---

## 6. Troubleshooting

| Symptom                                                              | Cause and remedy                                                                                                                              |
|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Service refuses to start; log says *missing required configuration*  | One of `vap_base_url`, `api_user`, `api_secret` is empty. Provide via config or env-var override.                                             |
| Service refuses to start; log says *config file ... has mode ...*    | Config file is readable by group/other. `chmod 0600` on Linux / restrict ACL on Windows.                                                      |
| Service refuses to start; log says *vap_base_url uses http://*       | Plain HTTP is permitted only with `http.tls_verify = false`, intended for dev only. Set the V.ap base URL to `https://` for production.       |
| Service refuses to start; log says *non-loopback... requires [access] secret* | `bind.address` is not loopback and no access secret is configured. Set `[access] secret`, or bind to `127.0.0.1` for the loopback model.  |
| Service refuses to start; log says *allowlist.paths entry must be an absolute path* | An `[allowlist].paths` entry is missing its leading `/`. Each entry must be an absolute upstream path (e.g. `/api/duba/v1/memento`). |
| Service starts but every request returns 502 `upstream_unavailable`  | The component cannot reach V.ap. Check DNS, firewall, proxy; rerun the curl check from [§4.2](#42-verify-vap-reachability).                   |
| Every request returns 502 `upstream_auth_failed`                     | `api_user` / `api_secret` do not match a valid V.ap API user. Confirm with your Vertama contact.                                              |
| Requests return 403 `access_denied`                                  | (Intranet deployment.) The `_s` URL parameter is missing or does not match the configured `[access] secret`. Verify the KIS template carries the correct `_s` value. |
| Requests return 404 `path_not_allowed`                               | The requested upstream path is not on the configured `[allowlist] paths` list. Either add the path or use the V.ap URL-builder tooling, which only emits allowlisted endpoints. |
| Requests return 400 `coercion_failed`                                | A typed parameter (date, boolean) was substituted by the KIS with an unacceptable value. Reproduce with the V.ap URL-builder live-test panel. |
| Requests return 422                                                  | V.ap validation rejected the payload. The response body carries V.ap's `errors[]` — read it for the field-level cause.                        |
| Browser follows the 303 but lands on the V.ap login page             | The `magicLink` token has expired or the API user is no longer authorised. Generate a fresh request.                                          |

For deeper diagnosis, increase log level to `debug`
(`log.level = "debug"` in config, or
`FREMDAUFRUF_LOG_LEVEL=debug` in env) and restart. Component logs
remain spec-compliant (no parameter values or keys leak) at any log
level.

---

## 7. Uninstallation

### Windows

```bat
sc stop Fremdaufruf
sc delete Fremdaufruf
rmdir /s /q "%PROGRAMFILES%\Vertama\fremdaufruf"
rmdir /s /q "%PROGRAMDATA%\Vertama\fremdaufruf"
```

If installed via MSI: use *Apps & Features* → uninstall, which
performs all of the above plus removes the MSI registration entry.

### Linux

```bash
sudo systemctl disable --now fremdaufruf
sudo rm /etc/systemd/system/fremdaufruf.service
sudo systemctl daemon-reload
sudo rm /usr/local/bin/fremdaufruf
sudo rm -rf /etc/vertama/fremdaufruf
sudo userdel fremdaufruf   # removes the service account
```

---

**Related documents:**

- [Overview](overview.md) — architecture and design rationale.
- [Benutzerhandbuch](user-manual.md) — KIS-integrator guide to the
  V.ap URL-builder tooling (DE).

---

**Last updated:** 2026-05-15
**Applies to:** V.connect Fremdaufruf V1
