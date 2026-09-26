import codecs

from fastapi import Request


async def log_requests(request: Request, call_next):
    print(f"--> {request.method} {request.url}")
    response = await call_next(request)

    original_iterator = response.body_iterator
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    print(f"<-- {response.status_code} {request.method} {request.url}")

    async def log_response_body():
        async for chunk in original_iterator:
            text = decoder.decode(chunk)
            if text:
                print(text, end="", flush=True)
            yield chunk
        remaining_text = decoder.decode(b"", final=True)
        if remaining_text:
            print(remaining_text, end="", flush=True)
        print()

    response.body_iterator = log_response_body()
    return response
