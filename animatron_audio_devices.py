import sounddevice as sd


def find_device_by_name(name_part, is_input=True):
    """Searches for a device containing name_part (case insensitive)."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if name_part.lower() in dev["name"].lower():
            if is_input and dev["max_input_channels"] > 0:
                return idx
            elif not is_input and dev["max_output_channels"] > 0:
                return idx
    raise ValueError(f"No '{is_input}' device found matching: '{name_part}'")


def get_audio_device_indices():
    mic_name = "UM02: USB Audio"
    speaker_name = "USB PnP Audio Device"

    mic_index = find_device_by_name(mic_name, is_input=True)
    speaker_index = find_device_by_name(speaker_name, is_input=False)

    print(f"Mic index: {mic_index} ({sd.query_devices(mic_index)['name']})")
    print(f"Speaker index: {speaker_index} ({sd.query_devices(speaker_index)['name']})")
    return {"mic_index": mic_index, "speaker_index": speaker_index}
