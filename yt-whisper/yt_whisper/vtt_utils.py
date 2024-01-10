"""Utilities for WEBVTT files"""

import re


def merge_webvtt_to_list(webvtt_str: str, merge_seconds: int) -> list[dict[str, str]]:
    """Merge WEBVTT text into a list of dictionaries with text and initial time"""

    # Split the WEBVTT text into lines and filter out empty lines
    lines = [line for line in webvtt_str.split("\n") if line.strip()]

    # Skip the first line which is just "WEBVTT"
    lines = lines[1:]

    # List to hold the final dictionaries
    result = []

    # Regular expression to match time and text
    time_regex = r"(\d{2}):(\d{2}):(\d{2})\.\d{3}"

    # Temporary variables to hold merged text and initial time
    merged_text = ""
    initial_time = 0
    current_block_time = 0

    for line in lines:
        # Check if line is a time line
        if "-->" in line:
            # Extract times
            times = re.findall(time_regex, line)
            start_time = (
                int(times[0][0]) * 3600 + int(times[0][1]) * 60 + int(times[0][2])
            )
            end_time = (
                int(times[1][0]) * 3600 + int(times[1][1]) * 60 + int(times[1][2])
            )

            # Update the initial time for the first block
            if not merged_text:
                initial_time = start_time

            # Update the current block's time
            current_block_time = end_time - initial_time
        else:
            # Append the line of text to the merged text
            merged_text += line + " "

            # Check if current block time exceeds the merge time
            if current_block_time >= merge_seconds:
                # Append to result and reset variables
                result.append(
                    {
                        "text": merged_text.strip(),
                        "initial_time_in_seconds": initial_time,
                    }
                )
                merged_text = ""
                initial_time = (
                    end_time  # Start new block from the end time of the previous block
                )

    # Add the last block if there is any text left
    if merged_text:
        result.append(
            {"text": merged_text.strip(), "initial_time_in_seconds": initial_time}
        )

    return result
