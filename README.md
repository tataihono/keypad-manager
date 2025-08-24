# Keypad Manager

A Home Assistant custom integration for managing keypad codes, RFID tags, and access permissions. This integration provides a centralized system for validating access attempts and controlling automations based on authorized users and schedules.

## Features

- **Code & Tag Management**: Manage keypad codes and RFID tags for multiple users
- **Schedule-based Access**: Control access based on time and day restrictions
- **Event-based Logging**: Native Home Assistant events for all access attempts
- **Automation Integration**: Easy integration with Home Assistant automations
- **User-friendly UI**: Web-based configuration interface
- **Security Monitoring**: Track successful and failed access attempts

## Installation

### HACS (Recommended)
1. Add this repository to HACS
2. Install the "Keypad Manager" integration
3. Restart Home Assistant
4. Add the integration via Configuration > Integrations

### Manual Installation
1. Copy the `custom_components/keypad_manager` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via Configuration > Integrations

## Configuration

### Basic Setup
1. Go to **Configuration** > **Integrations**
2. Click **+ Add Integration**
3. Search for **Keypad Manager**
4. Follow the setup wizard

### Adding Users
1. Open the Keypad Manager integration
2. Go to the **Users** tab
3. Click **Add User**
4. Enter the user's name, code, and/or tag
5. Set up access schedules if needed

### Automation Examples

#### Basic Code Validation
```yaml
automation:
  - alias: "Keypad Door Unlock"
    trigger:
      - platform: state
        entity_id: sensor.keypad_input
    action:
      - service: keypad_manager.validate_by_code
        data:
          code: "{{ states('sensor.keypad_input') }}"
          source: "front_door"
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ result.valid }}"
            sequence:
              - service: lock.unlock
                target:
                  entity_id: lock.front_door
```

#### Monitor Access Events
```yaml
automation:
  - alias: "Monitor Failed Access"
    trigger:
      - platform: event
        event_type: keypad_manager_code_failed
      - platform: event
        event_type: keypad_manager_tag_failed
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Security Alert"
          message: |
            Failed access attempt at {{ trigger.event.data.source }}
            Input: {{ trigger.event.data.code or trigger.event.data.tag }}
            Reason: {{ trigger.event.data.reason }}
```

## Services

### `keypad_manager.validate_by_code`
Validates a keypad code and returns success/failure.

**Parameters:**
- `code` (string, required): The numeric or alphanumeric code to validate
- `source` (string, optional): Where this validation request came from (e.g., 'front_door', 'garage', 'office')

**Returns:**
- `valid` (boolean): Whether the code is valid
- `user_name` (string, optional): Name of the user if valid
- `reason` (string): Reason for failure if invalid

### `keypad_manager.validate_by_tag`
Validates an RFID tag and returns success/failure.

**Parameters:**
- `tag` (string, required): The RFID tag ID to validate
- `source` (string, optional): Where this validation request came from (e.g., 'front_door', 'garage', 'office')

**Returns:**
- `valid` (boolean): Whether the tag is valid
- `user_name` (string, optional): Name of the user if valid
- `reason` (string): Reason for failure if invalid

## Events

The integration emits the following events:

- `keypad_manager_code_validated`: Successful code validation
- `keypad_manager_tag_validated`: Successful tag validation
- `keypad_manager_code_failed`: Failed code validation
- `keypad_manager_tag_failed`: Failed tag validation

## Support

- **Issues**: [GitHub Issues](https://github.com/tataihono/keypad-manager/issues)
- **Documentation**: [GitHub Repository](https://github.com/tataihono/keypad-manager)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
