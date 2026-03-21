# Cyber Shell

`cyber-shell` la local CLI wrapper cho Bash interactive tren Linux/Kali. Tool mo shell that trong PTY, giu lai shell feel cua user, dong thoi capture command/output/exit code/cwd de gui telemetry len endpoint noi bo theo che do fail-open.

## Tinh nang v1

- Spawn Bash interactive that trong PTY.
- Relay stdin/stdout theo raw terminal mode, co resize support.
- Hook `PS0` va `PROMPT_COMMAND` qua control pipe rieng, khong in marker vao terminal.
- Capture moi command thanh 1 event logic voi:
  - `cmd`
  - `output`
  - `exit_code`
  - `cwd`
  - `started_at`
  - `finished_at`
  - `is_interactive`
- Telemetry async, retry/backoff, timeout va fail-open.
- Gioi han `max_output_bytes` de tranh gui output vo han.
- Mock endpoint tich hop de local test.

## Cai dat

```bash
python3 -m pip install .
```

Hoac cho dev:

```bash
python3 -m pip install -e .
```

## Cau hinh

Mac dinh tool doc file:

```text
~/.config/cyber-shell/config.yaml
```

Tool ho tro format YAML toi gian (key/value, co the co block `metadata:` 1 cap) va env override.

File mau:

```yaml
endpoint_url: "http://127.0.0.1:8080/api/terminal-events"
api_key: "replace-me"
timeout_ms: 3000
retry_max: 3
retry_backoff_ms: 1000
max_output_bytes: 262144
queue_size: 256
user_id: "student-01"
lab_id: "lab-web-02"
target_id: "target-a"
metadata:
  hostname_group: "kali-lab"
```

Env override:

- `CYBER_SHELL_CONFIG`
- `CYBER_SHELL_ENDPOINT_URL`
- `CYBER_SHELL_API_KEY`
- `CYBER_SHELL_TIMEOUT_MS`
- `CYBER_SHELL_RETRY_MAX`
- `CYBER_SHELL_RETRY_BACKOFF_MS`
- `CYBER_SHELL_MAX_OUTPUT_BYTES`
- `CYBER_SHELL_QUEUE_SIZE`
- `CYBER_SHELL_USER_ID`
- `CYBER_SHELL_LAB_ID`
- `CYBER_SHELL_TARGET_ID`
- `CYBER_SHELL_SHELL_PATH`

## Cach chay

Bat mock endpoint o terminal A:

```bash
cyber-shell mock-endpoint --host 127.0.0.1 --port 8080
```

Mo dashboard xem event:

```text
http://127.0.0.1:8080/
```

Check nhanh service song:

```bash
curl -i http://127.0.0.1:8080/health
```

Mo wrapped shell o terminal B:

```bash
cyber-shell
```

Hoac:

```bash
cyber-shell start --config ~/.config/cyber-shell/config.yaml
```

Neu muon override bang env trong Bash, phai `export` hoac dat cung dong lenh:

```bash
export CYBER_SHELL_ENDPOINT_URL=http://127.0.0.1:8080/api/terminal-events
export CYBER_SHELL_API_KEY=replace-me
cyber-shell
```

Hoac:

```bash
CYBER_SHELL_ENDPOINT_URL=http://127.0.0.1:8080/api/terminal-events \
CYBER_SHELL_API_KEY=replace-me \
cyber-shell
```

Hoac:

```bash
cyber-shell --endpoint-url http://127.0.0.1:8080/api/terminal-events --api-key replace-me
```

De xac nhan dang o trong wrapped shell, chay:

```bash
echo $CYBER_SHELL_SESSION_ID
```

Neu co gia tri `sess-...` thi ban dang o trong session cua `cyber-shell`.

In file config mau:

```bash
cyber-shell print-default-config
```

Kich event thu cong (khong can mo wrapped shell):

```bash
curl -i -X POST http://127.0.0.1:8080/api/terminal-events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer replace-me" \
  -d '{"session_id":"s1","seq":1,"cmd":"whoami","cwd":"/home/kali","exit_code":0,"output":"kali","output_truncated":false,"started_at":"2026-03-21T10:00:00Z","finished_at":"2026-03-21T10:00:01Z","is_interactive":false,"hostname":"kali","shell":"bash","user_id":"student-01","lab_id":"lab-01","target_id":"t1","metadata":{}}'
```

## Luu y van hanh

- Tool chi chay tren POSIX/Linux. Muc tieu la Kali.
- V1 khong parse semantic cua `vim`, `top`, `nano`, `less`, `man`; chi dam bao chay duoc va finalize event khi prompt quay lai.
- Nested shell/remote shell duoc coi la opaque stream.
- Tool khong capture raw keystrokes toan phien.

## Kiem tra nhanh

```bash
python -m unittest discover -s tests -v
python -m compileall src tests
```
