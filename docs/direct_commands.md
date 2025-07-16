# Direct Commands in Chat Assistant

The Chat Assistant now supports direct action commands that bypass the AI model for faster and more precise control.

## Usage

Type commands starting with `#action` in the chat input, for example:

```
#action add flash to parcan_l at 5.2 duration 1.5
```

## Supported Commands

- `#action clear all` - Clear all actions from the current song
- `#action clear id <action_id>` - Clear a specific action by ID
- `#action clear group <group_id>` - Clear all actions with a specific group ID
- `#action add <action> to <fixture> at <start_time> duration <duration_time>` - Add a new action
- `#action render` - Render all actions to the DMX canvas

## Examples

```
#action add flash to parcan_l at 5.2 duration 1.5
#action add strobe to moving_head at 10 duration 2
#action clear all
#action render
```

## Notes

- All times are in seconds
- You need to have a song loaded for these commands to work
- After adding actions, use `#action render` to see the results
- Direct commands appear in purple in the chat interface
