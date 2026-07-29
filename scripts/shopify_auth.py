"""
Shopify Admin API auth, shared by the scripts in this folder.

THREE WAYS IN, tried in this order:

  1. SHOPIFY_ADMIN_TOKEN — a token you already hold. Used as-is.

  2. SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET — exchanged for a token via the
     client credentials grant. This is the path for CI.

  3. The Shopify CLI. Convenient locally because there is nothing to configure,
     but it needs an interactive login so it does not work in CI.

WHY THE EXCHANGE MATTERS. Shopify no longer shows an Admin API token in the
admin UI; custom apps now hand out a Client ID and Secret which you exchange for
a token. Crucially, that token **expires in 24 hours**. Storing one in GitHub
Secrets would work today and silently fail tomorrow — the kind of breakage that
looks like "the job ran and found nothing" rather than an error. So CI stores the
ID and secret, and every run mints a fresh token.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

STORE = os.environ.get("SHOPIFY_STORE", "9wgxci-qu.myshopify.com")
API_VERSION = "2025-07"

_cached_token = None


def _exchange_client_credentials(client_id, client_secret):
    """Trade a Client ID and Secret for a short-lived Admin API token."""
    req = urllib.request.Request(
        f"https://{STORE}/admin/oauth/access_token",
        data=json.dumps({
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        sys.exit(
            "Client credentials exchange failed "
            f"({exc.code}): {exc.read().decode(errors='replace')[:300]}\n"
            "Check that the app is installed on the store and that the ID and "
            "secret belong to it."
        )
    except urllib.error.URLError as exc:
        sys.exit(f"Could not reach Shopify to exchange credentials: {exc}")

    token = payload.get("access_token")
    if not token:
        sys.exit(f"Exchange returned no access_token: {json.dumps(payload)[:300]}")
    return token


def resolve_token():
    """The token to use, or None to fall back to the CLI."""
    global _cached_token
    if _cached_token:
        return _cached_token

    direct = os.environ.get("SHOPIFY_ADMIN_TOKEN")
    if direct:
        _cached_token = direct
        return _cached_token

    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    if client_id and client_secret:
        _cached_token = _exchange_client_credentials(client_id, client_secret)
        return _cached_token

    return None


def gql(query, mutation=False):
    """Run a GraphQL operation and return the `data` object.

    `mutation` only matters for the CLI path, which requires an explicit flag
    before it will run one.
    """
    token = resolve_token()

    if token:
        req = urllib.request.Request(
            f"https://{STORE}/admin/api/{API_VERSION}/graphql.json",
            data=json.dumps({"query": query}).encode(),
            headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            sys.exit(f"Admin API {exc.code}: {exc.read().decode(errors='replace')[:400]}")
        except urllib.error.URLError as exc:
            sys.exit(f"Admin API request failed: {exc}")

        if "errors" in payload:
            sys.exit(f"Admin API returned errors: {json.dumps(payload['errors'])[:400]}")
        return payload.get("data", {})

    cmd = ["shopify", "store", "execute", "-s", STORE, "--json", "-q", query]
    if mutation:
        cmd.append("--allow-mutations")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout
    if "{" not in out:
        sys.exit(
            "No Shopify credentials and the CLI returned nothing.\n"
            "Set SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET, or run "
            f"`shopify store auth --store {STORE} --scopes ...`.\n\n{out}\n{proc.stderr}"
        )
    try:
        return json.loads(out[out.index("{"):])
    except json.JSONDecodeError:
        sys.exit(f"Could not parse Shopify CLI response:\n{out[:1500]}")
