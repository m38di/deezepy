"""OAuth server-side flow + authenticated actions.

Fill in APP_ID / APP_SECRET / REDIRECT_URI, run the script, open the printed
URL, approve the app, then paste the ``code`` back. Nothing is stored.
"""

from deezify import DeezerClient, authorization_url

APP_ID = "YOUR_APP_ID"
APP_SECRET = "YOUR_APP_SECRET"  # never ship this in client-side/distributed code
REDIRECT_URI = "https://your-app.example/callback"


def main() -> None:
    url = authorization_url(
        APP_ID,
        REDIRECT_URI,
        perms="basic_access,email,offline_access,manage_library",
        state="csrf-token-change-me",
    )
    print("Open this URL and approve the app:\n")
    print(url)
    code = input("\nPaste the ?code= value Deezer sent to your redirect_uri: ").strip()

    client = DeezerClient()
    token = client.exchange_code_for_token(APP_ID, APP_SECRET, code)
    print("Token response keys:", sorted(token))
    client.set_access_token(token["access_token"])

    me = client.user.me()
    print(f"Hello, {me['name']}!")

    playlist = client.user.create_playlist("me", "deezify demo")
    print("Created playlist:", playlist.get("id"))
    client.playlist.add_tracks(playlist["id"], [3135556])
    print("Added a track. Listening history:")
    for t in client.user.history(limit=3):
        print(f"  - {t['title']}")


if __name__ == "__main__":
    main()

