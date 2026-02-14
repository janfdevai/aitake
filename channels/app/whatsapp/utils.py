def remove_extra_one(from_number: str) -> str:
    if "1" not in from_number[:2]:
        return from_number[:2] + from_number[3:]
    return from_number

async def process_message_type(message: dict) -> str:
    if "text" in message:
        return message["text"]["body"]
    elif "location" in message:
        return str(message["location"])
    return "message not processed"
