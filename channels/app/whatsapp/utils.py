def remove_extra_one(from_number: str) -> str:
    """
    Removes the extra '1' in Mexican numbers (e.g., 521... -> 52...).
    Only applies if the number starts with '521'.
    """
    # Remove any non-digit characters (like '+', '-', ' ')
    clean_number = "".join(filter(str.isdigit, from_number))
    
    if clean_number.startswith("521") and len(clean_number) > 3:
        return "52" + clean_number[3:]
    return clean_number

async def process_message_type(message: dict) -> str:
    if "text" in message:
        return message["text"]["body"]
    elif "location" in message:
        return str(message["location"])
    return "message not processed"
