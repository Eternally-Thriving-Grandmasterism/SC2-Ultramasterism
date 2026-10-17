# `api_bot_vs_easy_ai.SC2Replay.b64`

A replay saved through the StarCraft II API by `python -m sc2um.bot play`
(this repository's bot vs the built-in Easy AI, which rolled Zerg, on
AcropolisLE, Linux client 4.10.0.75689, 2026-10-17). The bot won in 6:13.
It is used to test that the replay engine can read API-saved replays
(see `sc2um/bot/replay_compat.py`).

- SHA-256 of the decoded file: `f076270e789182710945081f5a3b75711576f63f7ceab5a3b79fafcdcbc84d26`
- Stored base64-encoded; `base64 -d api_bot_vs_easy_ai.SC2Replay.b64 > x.SC2Replay` restores it.

It was generated with Blizzard's StarCraft II Linux client under the
[AI and Machine Learning License](http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html),
which lets the user own and use data generated through authorised use of
the software (section 2.A). No game files or maps are included.
