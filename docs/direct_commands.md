# Direct Commands in Chat Assistant

The Chat Assistant now supports direct action commands ("Direct Commands") that bypass the AI model for faster and more precise control.

## Usage

Type commands starting with `#` in the chat input, for example:

```
#add flash to parcan_l at 5.2 duration 1.5
#add strobe to moving_head at 10 duration 2
#add flash to parcan_l at 5.2 for 1.5
#clear all actions
#clear action 123
#clear group chorus
#render
#analyze
#analyze context
#help
```

## Supported Commands

- `#help` - Show a list of available commands
- `#clear all actions` - Clear all actions from the current song
- `#clear action <action_id>` - Clear a specific action by ID
- `#clear group <group_id>` - Clear all actions with a specific group ID
- `#add <action> to <fixture> at <start_time> duration <duration_time>` - Add a new action. Duration is optional, default is 1 beat.
- `#add <action> to <fixture> at <start_time> for <duration_time>` - Add a new action. Duration is optional, default is 1 beat.
- `#render` - Render all actions to the DMX canvas
- `#analyze` - Analyze the current song using the analysis service
- `#analyze context` - Generate lighting context for the current song using AI (shows progress)

## Accepted Time Formats

- `1m23.45s` (1 minute 23.45 seconds)
- `2b` (duration of 2 beats at the BPM of the current song)
- `12.5` (seconds)

## Notes

- All times are converted to seconds automatically
- You need to have a song loaded for these commands to work
- After adding actions, use `#render` to see the results
- Direct commands appear in purple in the chat interface
