# Roblox Account Generator

Threaded Roblox account generator using FunBypass for FunCaptcha solving.
Uses real browser TLS impersonation (`primp` + `curl_cffi`), the Roblox
`secureAuthenticationIntent` flow, and proxy-consistent captcha solving.

## Setup

```bash
cd generator
pip3 install -r requirements.txt
```

## Configure

- `input/config.json` — your FunBypass `solverKey` and thread count.
- `input/proxies.txt` — one proxy per line, format `socks5://user:pass@host:port`
  (HTTP/SOCKS5 both work; residential recommended).

## Run

```bash
./run.sh
# or:
python3 src/main.py
```

Must be run from the `generator/` directory (paths are relative).

## Output

- `output/accounts.txt` — `username:password:cookie`
- `output/cookies.txt` — `.ROBLOSECURITY` cookies

## Notes

- Failed FunBypass tasks are auto-refunded, so retries on solve failures are cheap.
- If you see `Rate limited`, the proxy IP hit Roblox's limit — add more proxies.
