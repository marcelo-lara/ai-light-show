def string_to_time(string: str) -> float:
    """
    Convert a time string in the format '1m0.05s' or 'MM:SS.sss' to seconds (float).
    
    Args:
        string (str): Time string to convert.
        
    Returns:
        float: Time in seconds.
    """
    if not string:
        return 0.0
    try:

      # Handle '1m0.05s' format
      if 'm' in string and 's' in string:
          minutes, seconds = string.split('m')
          seconds = seconds.replace('s', '')
          return float(minutes) * 60 + float(seconds)

      # Handle '3.4s' format
      if string.endswith('s'):
          return float(string[:-1])
      
      # Handle 'MM:SS.sss' format
      if ':' in string:
          parts = string.split(':')
          if len(parts) == 2:
              minutes, seconds = parts
              return float(minutes) * 60 + float(seconds)
    except ValueError:
        print(f"⚠️ Error converting time string '{string}' to seconds")
        return 0.0

    # If no recognizable format, assume it's already in seconds
    return float(string)

def beats_to_seconds(n_beats: float, tempo: float) -> float:
    """
    Convert beats to seconds based on the tempo.
    
    Args:
        n_beats (float): Number of beats.
        tempo (float): Tempo in beats per minute (BPM).
        
    Returns:
        float: Time in seconds.
    """
    if tempo <= 0:
        print(f"⚠️ Invalid tempo: {tempo}. Tempo must be positive.")
        return 0.0
    return n_beats / tempo * 60
