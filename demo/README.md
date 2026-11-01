# Demo assets

- **`walkthrough-script.md`** — timed 45-second shot list + narration.
- **`walkthrough.gif`** — screen recording (10 frames, 1490×786) of the full
  flow: Overview → Agents → run a task → live tool-call timeline → the
  **human-approval gate** on `send_notification` → Approve → completion.
- Screenshot view list in [`../screenshots`](../screenshots).

To re-record with Claude-in-Chrome: `gif_creator start_recording`, run the flow
in `walkthrough-script.md`, `stop_recording`, then `export` with
`download: true` and move the file here as `walkthrough.gif`.
